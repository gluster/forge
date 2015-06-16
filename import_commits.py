#!/usr/bin/env python
"""Process the commit history of an existing git repo

Adds each commit, from each branch, into a database for cross-repo analysis

Requires the Python SQLite3 and PyGit2 modules

DB structure:
  + repo table
      repo_id : int
      name : text
  + people table
      people_id : int (auto-incremented value, created by the database on each insert of NULL for this field)
      name : text
      email : text
  + commits table
      commit_id : int
      commit_time : text (only accurate to the second)
      repo : int (should have a foreign constraint ensuring it's in the repo table)
      author: int (should have a foreign constraint ensuring it's in the people table)
      hash : text (long hash.  Should be unique in a given repo, but may not be when several repos are considered)
      message : text (the commit message)
"""

# TODO: At the moment the code doesn't select any particular branch.  So find out if it's selecting only from master,
#       or if it's selecting across all branches.  Then make sure all commits (across all branches) are captured
#       Seems like the info needed is here: http://www.pygit2.org/references.html
# TODO: Detect repos newly added to the config file, automatically clone them locally, process them, then (maybe: TBD)
#       remove the local clone

from datetime import datetime
import os, os.path, sys, ConfigParser
import subprocess
import sqlite3
from pygit2 import clone_repository, Repository, GIT_SORT_TIME, GIT_SORT_REVERSE

# Set to False to turn off debugging info.  Set to 1 for git log style output. Set to 2 for commit insert info only
# TODO: Turn this into a bitmask using defined constants, for more fine grained control of debug output
debug = 2

# Read the GitHub projects from the ./config file
base_path = os.path.dirname(os.path.realpath(__file__))
config_file_path = os.path.join(base_path, 'config')
config = ConfigParser.SafeConfigParser()
config.read(config_file_path)

# Open the ./db/project_stats.db SQLite3 database
db_path = os.path.join(base_path, 'db/project_stats.db')
conn = sqlite3.connect(db_path)

# Connect to the database
c = conn.cursor()

# Create the database tables to store the commit info, if they're not already present
sql = 'CREATE TABLE IF NOT EXISTS repo (repo_id INTEGER PRIMARY KEY, name TEXT)'
c.execute(sql)

sql = 'CREATE TABLE IF NOT EXISTS people (people_id INTEGER PRIMARY KEY, name TEXT, email TEXT)'
c.execute(sql)

sql = 'CREATE TABLE IF NOT EXISTS commits (commit_id INTEGER PRIMARY KEY, commit_time TEXT, repo INTEGER, ' \
       'author INTEGER, hash TEXT, message TEXT)'
c.execute(sql)
conn.commit()

# Create indices for the tables, if they're not already present
sql = 'CREATE INDEX IF NOT EXISTS people_email ON people (email)'
c.execute(sql)

sql = 'CREATE INDEX IF NOT EXISTS commits_time ON commits (commit_time)'
c.execute(sql)

sql = 'CREATE INDEX IF NOT EXISTS commits_hash ON commits (hash)'
c.execute(sql)

sql = 'CREATE INDEX IF NOT EXISTS commits_author ON commits (author)'
c.execute(sql)

conn.commit()


# Loop through the projects in the config file
for repo_name in config.sections():

    # Attempt to open an existing local repo
    try:
        local_dir = os.path.join(base_path, 'repos', repo_name + '.git')
        repo = Repository(local_dir)

        # Fetch the latest commits (equivalent to "git fetch origin")
        progress = repo.remotes["origin"].fetch()

        # Update HEAD with the new commits (equivalent to "git update-ref HEAD FETCH_HEAD")
        # TODO: This should be tweaked to update all branches, not just the default one
        head = repo.head
        fetch_head = repo.lookup_reference('FETCH_HEAD')
        new_head = head.set_target(fetch_head.target)

        # Notice new branches added to the origin
        os.chdir(local_dir)
        update_result = subprocess.call(["git", "remote", "update", "origin"])

        # Prune local branches no longer present on the origin
        prune_result = subprocess.call(["git", "remote", "prune", "origin"])

        # Run git gc, to stop potential unlimited repo growth from accumulating dead objects over time
        gc_result = subprocess.call(["git", "gc"])

    except KeyError:

        # Opening a local repo failed, so we assume it's not been cloned yet.  Do the cloning now
        repo_url = 'https://github.com/' + repo_name + '.git'
        repo = clone_repository(repo_url, local_dir, bare = True)

    except Exception, e:

        # Exit on all other exceptions
        print "An unknown error occurred on the {0} repo:\n\n\t{1}".format(repo_name, e.message)
        sys.exit(1)

    # Check if the repo is already in the database
    sql = 'SELECT repo_id, name FROM repo WHERE name = :repo_name'
    c.execute(sql, {"repo_name": repo_name})
    result = c.fetchall()
    if len(result) > 0:
        # The unique id # for the repo in the database
        repo_id = result[0][0]
    else:
        # The repo isn't in the database yet, so we add it
        sql = 'INSERT INTO repo (repo_id, name) VALUES (NULL, :repo_name)'
        c.execute(sql, {"repo_name": repo_name})
        conn.commit()

        # Retrieve the repo_id value generated by the database for the above insert
        repo_id = c.lastrowid

    # Starting with the oldest commit in the repo, add all commits to the database
    for commit in repo.walk(repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):

        # If requested, display the commit info for debugging purposes
        if debug == 1:
            print "commit {0}".format(commit.hex)
            print "Author: {0} <{1}>".format(unicode(commit.author.name).encode("utf-8"), commit.author.email)
            print datetime.utcfromtimestamp(commit.commit_time).strftime('Date:   %Y-%m-%d %H:%M:%S\n')
            print "   {0}".format(unicode(commit.message).encode("utf-8"))

        # Check if the commit already exists in the database.  Don't add it if its already there
        sql = 'SELECT commit_id, hash FROM commits WHERE repo = :repo AND hash = :hash'
        c.execute(sql, {"repo": repo_id, "hash": commit.hex})
        result = c.fetchall()
        if len(result) > 0:

            # If requested, show debugging info
            if debug == 2:
                print "{0} - Commit {1} already present in the database".format(repo_name, commit.hex)

        else:
            ### The commit isn't yet in the database, so add it

            # Check if the author already exists in the database
            sql = 'SELECT people_id, email FROM people WHERE email = :email_addr'
            c.execute(sql, {"email_addr": commit.author.email})
            result = c.fetchall()
            if len(result) > 0:
                # The unique id # for the author in the database
                author_id = result[0][0]
            else:
                # The author isn't in the database yet, so we add them
                sql = 'INSERT INTO people (people_id, name, email) VALUES (NULL, :author_name, :email_addr)'
                c.execute(sql, {"author_name": commit.author.name, "email_addr": commit.author.email})
                conn.commit()

                # Retrieve the people_id value generated by the database for the above insert
                author_id = c.lastrowid

                # If requested, show debugging info
                if debug == 2:
                    print "{0} - Author {1} added to database".format(repo_name, unicode(commit.author.name).encode("utf-8"))

            # Insert the commit data into the database
            sql = ('INSERT INTO commits (commit_id, commit_time, repo, author, hash, message) VALUES '
                   '(NULL, :commit_time, :repo, :author, :hash, :message)')
            c.execute(sql, {"commit_time": datetime.utcfromtimestamp(commit.commit_time).strftime('%Y-%m-%d %H:%M:%S'),
                            "repo": repo_id, "author": author_id, "hash": commit.hex, "message":commit.message})
            conn.commit()

            # If requested, show debugging info
            if debug == 2:
                print "{0} - Commit {1} added to database".format(repo_name, commit.hex)

# Close the database connection
c.close()
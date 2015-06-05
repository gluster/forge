#!/usr/bin/env python
"""Collect the latest social stats for Gluster projects

Grabs watchers, stars, forks, # of commits per day, and total number of downloads (ever).

Requires the SQLite3 Python module, and githubpy

  $ pip install githubpy
"""

import datetime
import os, os.path, ConfigParser
import sqlite3
from github import GitHub

# Enable this to have the results printed to stdout
debug = True

# Read the GitHub projects from the ./config file
base_path = os.path.dirname(os.path.realpath(__file__))
config_file_path = os.path.join(base_path, 'config')
config = ConfigParser.SafeConfigParser()
config.read(config_file_path)

# Read the GitHub auth info
token_path = os.path.expanduser('~/.gluster_forge_credentials')
token_file = ConfigParser.SafeConfigParser()
token_file.read(token_path)
token = token_file.get('personal_token', 'token')

# Authenticate to GitHub using my generated Personal Access token as per https://github.com/settings/tokens
gh = GitHub(access_token=token)

# Open the ./db/project_stats.db SQLite3 database
db_path = os.path.join(base_path, 'db/project_stats.db')
conn = sqlite3.connect(db_path)

# Connect to the database
c = conn.cursor()

# Create the SQLite3 table to store the info, if it's not already present
sql = ('CREATE TABLE IF NOT EXISTS social_stats (project TEXT, time_stamp TEXT, '
       'watchers INTEGER, stars INTEGER, forks INTEGER, commits INTEGER, downloads INTEGER)')
c.execute(sql)
conn.commit()

# Loop through the projects in the config file
for project in config.sections():

    # Extract the number of watchers, stars, and forks on GitHub
    repo_data = gh.repos(project).get()
    watchers = repo_data['subscribers_count']
    stars = repo_data['stargazers_count']
    forks = repo_data['forks_count']

    # Count the # of commits in the last 24 hours
    now = datetime.datetime.utcnow()
    yesterday = now + datetime.timedelta(days=-1)
    commits = gh.repos(project).commits.get(since=yesterday)
    commits_count = len(commits)

    # Count how many downloads have occurred (ever) for the project
    # Note - For each project there is an outer loop of "releases" (eg v3.6.0), with an inner loop of "assets" inside
    # each release (with each asset having it's own download counter). eg: an .exe and a .dmg might be two assets in
    # the same v3.6.0 release.  The .exe might have 10,000 downloads, and the .dmg might have 3,000.
    download_counter = 0
    releases = gh.repos(project).releases.get()
    for release in releases:
        for asset in release['assets']:
            download_counter += asset['download_count']

    # Print the results to stdout
    if debug:
        print ('{0}\n\tcommits: {1}\twatchers: {2}\tstars: {3}\tforks: {4}\t'
               'downloads: {5}\n'.format(project, commits_count, watchers, stars, forks, download_counter))

    # Add the results to the database
    sql = ('INSERT INTO social_stats (project, time_stamp, watchers, stars, forks, commits, downloads) VALUES '
           "('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')").format(project, now, watchers, stars, forks,
                                                                       commits_count, download_counter)
    c.execute(sql)
    conn.commit()

# Close the database connection
c.close()
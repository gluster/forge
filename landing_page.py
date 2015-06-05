#!/usr/bin/env python
"""Generate the landing page for the Gluster Forge

Generates the content, leaving the look/feel to be controlled
by CSS (untouched by this).  This should mean other people can
generate CSS that looks good, without needing to touch this
code.  (in theory ;>)

Requires the SQLite3 Python module
"""

import os, os.path, sys, ConfigParser
import sqlite3
import requests
import json
from datetime import datetime

# Info to grab

## Incubating Projects

## Active Projects

# Open the ./db/project_stats.db SQLite3 database
base_path = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(base_path, 'db/project_stats.db')
conn = sqlite3.connect(db_path)

# Connect to the database
c = conn.cursor()

# Retrieve all of the project stats for the last day
sql = ("select * from social_stats where time_stamp > strftime('%Y-%m-%dT%H:%M:%S', 'now', '-1 day')")
c.execute(sql)
sql_results = c.fetchall()

# Close the database connection
c.close()

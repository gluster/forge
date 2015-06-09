# Gluster Forge v2

Source code for the Gluster Forge v2

## Setup

To make this work, a (small) amount of setup needs to be done first:

**1**. Generate a GitHub auth token for yourself [here](https://github.com/settings/tokens).<br />
**2**. Add the token to ~/.gluster_forge_credentials

Create a text file called ".gluster_forge_credentials" in your user home directory.

The file contents need to be:

    [personal_token]
    token = YOUR_API_TOKEN_GENERATED_ABOVE

eg:

    [personal_token]
    token = a49040f62a12c9e7795f2bb4da86d3cd02e80ca2

This token is used for authentication to the GitHub API, to avoid hitting the (low) rate limit ceiling for unauthenticated requests.

**3**. Add collect_latest_stats.py to a cronjob

The [stats collector script](https://github.com/gluster/forge/blob/master/collect_latest_stats.py) should
run from cron as often as desired.  eg hourly/daily/whatever-you-decide.

The script **does not** need root access, and will run fine from a user account.

Example crontab line:

    25 * * * * /home/jclift/git_repos/forge/collect_latest_stats.py

## Adding further projects to stats collection

The '[config](https://github.com/gluster/forge/blob/master/config)' file holds the org/project names to collect stats for.  Each org/project pair goes on a separate line, and should be inside square brackets - "[org_name/project_name]". eg:

    [gluster/glusterfs]
    [justinclift/glusterflow]
    [pcuzner/gstatus]
    [purpleidea/puppet-gluster]

To add further projects, just add them to this the file (keep it alphabetical).

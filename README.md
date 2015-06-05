# Gluster Forge v2

Source code for the Gluster Forge v2

## Setup

To make this work, a (small) amount of setup needs to be done first:

1. Generate a GitHub auth token for yourself [here](https://github.com/settings/tokens).
2. Create a text file called ".gluster_forge_credentials" in your user home directory. (eg ~/.gluster_forge_credentials)

The file contents need to be:

    [personal_token]
    token = YOUR_API_TOKEN_GENERATED_ABOVE

eg:

    [personal_token]
    token = a49040f62a12c9e7795f2bb4da86d3cd02e80ca2

This token is used for authentication to the GitHub API, to avoid hitting the (low) rate limit ceiling for unauthenticated requests.

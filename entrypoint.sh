#!/bin/bash
set -e

# Allow overriding the secrets directory for flexibility/testing
# Defaults to /run/secrets
SECRETS_DIR=${SECRETS_DIR:-/run/secrets}

# Check if secrets directory exists
if [ -d "$SECRETS_DIR" ]; then
    # Loop over the secrets
    for file in "$SECRETS_DIR"/*; do
        if [ -f "$file" ]; then
            key=$(basename "$file")
            # Read the file content
            # Command substitution $(cat file) strips trailing newlines
            val=$(cat "$file")
            
            # Export valid env var (simplified approach)
            export "$key"="$val"
        fi
    done
else
    echo "Warning: Secrets directory '$SECRETS_DIR' not found. Skipping secret injection." >&2
fi

# Execute the command passed to the docker container
exec "$@"

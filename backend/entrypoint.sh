#!/bin/bash
set -e

echo "--- Starting Secret Injection ---"

SECRETS_DIR=${SECRETS_DIR:-/run/secrets}

echo "Checking directory: $SECRETS_DIR"

if [ -d "$SECRETS_DIR" ]; then
    echo "Directory found. Listing files..."
    ls -la "$SECRETS_DIR"
    
    for file in "$SECRETS_DIR"/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            
            # Convert to UPPERCASE
            key=$(echo "$filename" | tr '[:lower:]' '[:upper:]')
            
            # Read value
            val=$(cat "$file")
            
            echo "Exporting secret: $key"
            export "$key"="$val"
        else
            echo "Skipping non-file: $file"
        fi
    done
else
    echo "Secrets directory not found!"
fi

echo "--- Finished Injection. Executing command: $@ ---"

# Verify export works in this shell before handoff
env | grep "BACKEND_API_KEY" || echo "WARNING: BACKEND_API_KEY not found in env before exec!"

exec "$@"
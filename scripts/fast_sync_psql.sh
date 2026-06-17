#!/bin/bash
# scripts/fast_sync_psql.sh
# Performs a high-speed data import from SQL dump using a temporary 'stage' schema.

set -e

# Configuration
DB_URL="postgresql://postgres:gFcbjZtsnKkPQoeyKnOYtXchfxMSQGPZ@acela.proxy.rlwy.net:37455/railway"
# Extract standard URL from async version if needed
DUMP_FILE="production-dump.sql"
STAGE_DUMP="production-dump-stage.sql"
MERGE_SQL="scripts/merge_stage_to_public.sql"

if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: $DUMP_FILE not found."
    exit 1
fi

echo "--- FAST SYNC START ---"

echo "1. Creating clean public and stage schemas..."
psql "$DB_URL" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"
psql "$DB_URL" -c "DROP SCHEMA IF EXISTS stage CASCADE; CREATE SCHEMA stage;"

echo "2. Applying schema to public..."
psql "$DB_URL" -q -f "scripts/schema.sql"

echo "3. Preparing dump file (redirecting to stage schema)..."
# Replace explicit 'public.' prefixes with 'stage.'
sed 's/public\./stage./g' "$DUMP_FILE" > "$STAGE_DUMP"

echo "4. Loading dump into stage schema (this may take a few seconds)..."
psql "$DB_URL" -q < "$STAGE_DUMP"

echo "5. Merging data from stage to public table by table..."
# We run psql with -a (echo all) to see progress, but it might be too noisy. 
# Better run it normally.
psql "$DB_URL" -f "$MERGE_SQL"

echo "6. Cleaning up stage schema..."
psql "$DB_URL" -c "DROP SCHEMA stage CASCADE;"
rm "$STAGE_DUMP"

echo "--- FAST SYNC COMPLETE ---"
echo "Check counts with: python check_counts.py"

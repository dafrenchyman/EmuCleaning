#!/bin/bash

# Download the gamesdb database
wget -q --show-progress http://cdn.thegamesdb.net/tgdb_dump.zip --output-document=./database/tgdb_dump.zip

# Extract only the file we need from it
unzip -j "./database/tgdb_dump.zip" "home/mysqldumps/tgdb.sql" -d "./database/"

# Convert it to sqlite
./tools/mysql2sqlite ./database/tgdb.sql | sqlite3 ./database/tgdb.db
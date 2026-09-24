#!/bin/bash

# Step 1: Download the gzip file
wget "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DB0250EN-SkillsNetwork/labs/Bash%20Scripting/ETL%20using%20shell%20scripting/web-server-access-log.txt.gz"

# Step 2: Unzip the file
gunzip -f web-server-access-log.txt.gz

# Step 3: Extract the first four fields (timestamp, latitude, longitude, visitorid)
# Step 4: Redirect output into extracted-data.txt
cut -d"#" -f1-4 web-server-access-log.txt > extracted-data.txt

# Step 5: Transform into CSV format (replace '#' with ',')
tr "#" "," < extracted-data.txt > extracted-data.csv

# Step 5: Load into PostgreSQL using COPY command
sudo -u postgres psql -d first_cron_job <<EOF
COPY access_log(timestamp, latitude, longitude, visitorid)
FROM '$(pwd)/extracted-data.csv'
DELIMITER ','
CSV HEADER;
EOF

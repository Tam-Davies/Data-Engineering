# PostgreSQL Database Cron Job

This folder contains a Bash ETL job that downloads a web-server access log, extracts the fields needed by PostgreSQL, converts the data to CSV, and loads it into an `access_log` table.

## Contents

- `cp-access-log.sh` - Bash ETL script.
- `web-server-access-log.txt` - Source access log, using `#` as the field delimiter.
- `extracted-data.txt` - Extracted timestamp, latitude, longitude, and visitor ID fields.
- `extracted-data.csv` - CSV version of the extracted data, ready for PostgreSQL.
- `.pgpass` - PostgreSQL connection-file placeholder. Do not commit credentials stored in this file.

## Requirements

- Bash
- `wget`
- `gunzip`
- PostgreSQL with the `psql` client
- A PostgreSQL database named `first_cron_job`
- A table named `access_log` with these columns:

```sql
CREATE TABLE access_log (
    timestamp timestamp,
    latitude numeric,
    longitude numeric,
    visitorid text
);
```

The script runs `psql` as the operating-system `postgres` user, so that user must be able to connect to the database and insert into the table.

## Run the ETL Job

Run the script from this folder because it uses relative paths for the downloaded and generated files:

```bash
cd /path/to/Postgres\ Database\ CRON\ Job
bash cp-access-log.sh
```

The script performs these steps:

1. Downloads `web-server-access-log.txt.gz` from the course data URL.
2. Decompresses the file into `web-server-access-log.txt`.
3. Keeps the first four `#`-delimited fields and writes them to `extracted-data.txt`.
4. Replaces `#` with commas and writes `extracted-data.csv`.
5. Loads the CSV into `access_log` using PostgreSQL `COPY`.

Verify the load with:

```bash
sudo -u postgres psql -d first_cron_job \
  -c "SELECT COUNT(*) FROM access_log;"
```

To inspect a few loaded records:

```bash
sudo -u postgres psql -d first_cron_job \
  -c "SELECT * FROM access_log LIMIT 10;"
```

## Schedule With Cron

Make the script executable:

```bash
chmod +x /path/to/Postgres\ Database\ CRON\ Job/cp-access-log.sh
```

Edit the crontab for the user that can run `sudo -u postgres psql`:

```bash
crontab -e
```

For example, to run the job every day at 01:00 and append output to a log file:

```cron
0 1 * * * cd /path/to/Postgres\ Database\ CRON\ Job && /bin/bash cp-access-log.sh >> cron-job.log 2>&1
```

Cron provides a limited environment. Use absolute paths for commands if they are not available through the cron user's `PATH`, and confirm that the cron user has permission to write in this folder.

## PostgreSQL Authentication

If password authentication is required, configure PostgreSQL credentials through the account's `.pgpass` file instead of placing a password in the script. The file must use this format:

```text
hostname:port:database:username:password
```

On Linux or WSL, restrict the file permissions:

```bash
chmod 600 ~/.pgpass
```

Do not commit real passwords or other secrets to this repository.

## Notes and Limitations

- Re-running the script downloads and overwrites the local source and generated files.
- The `COPY` command appends rows; it does not truncate or deduplicate `access_log` first. Repeated runs can therefore create duplicate records.
- The script assumes the downloaded file has the expected header and delimiter format.
- The source URL must be reachable from the machine running the cron job.
- The Bash script is intended for Linux, macOS, WSL, or another Unix-like environment. On Windows, use WSL or Git Bash with PostgreSQL tools available in the environment.

## PostgreSQL WSL–pgAdmin Troubleshooting

During the ETL setup, the Bash script initially failed to connect to PostgreSQL because the `postgres` user was configured for peer authentication.

### Issues Encountered

1. **Peer authentication failed**

  ```text
  FATAL: Peer authentication failed for user "postgres"
  ```

  **Solution:** Run PostgreSQL commands as the Linux `postgres` user:

  ```bash
  sudo -u postgres psql
  ```

2. **Database did not exist**

  ```text
  FATAL: database "first_cron_job" does not exist
  ```

  **Solution:** Create the database and required `access_log` table:

  ```bash
  sudo -u postgres createdb first_cron_job
  ```

3. **Database was not visible in pgAdmin**

  The Bash script was using PostgreSQL running inside **WSL**, while pgAdmin was connected to a separate **Windows PostgreSQL** instance.

4. **WSL PostgreSQL was only listening on localhost**

  Initially, PostgreSQL was listening on:

  ```text
  127.0.0.1:5432
  ```

  PostgreSQL 18 was configured to listen only on localhost.

  **Solution:** Update `/etc/postgresql/18/main/postgresql.conf` from:

  ```text
  #listen_addresses = '*'
  ```

  to:

  ```text
  listen_addresses = '*'
  ```

  Restart PostgreSQL and verify the listening address:

  ```bash
  sudo service postgresql restart
  sudo ss -ltnp | grep 5432
  ```

  Final result:

  ```text
  0.0.0.0:5432
  ```

### Final Setup

```text
Windows
  |
  +-- pgAdmin
      |
      | 172.19.81.167:5432
      v
    WSL
      |
      +-- PostgreSQL 18
          |
          +-- first_cron_job
              +-- access_log
```

This troubleshooting process highlighted the importance of understanding the difference between **PostgreSQL authentication, database instances, network interfaces, and client tools such as pgAdmin**.
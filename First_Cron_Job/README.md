# First Cron Job

This folder contains a small Bash backup job. The script creates a compressed archive of files that have been modified in the last 24 hours and places the archive in a destination directory.

## Contents

- `backup.sh` - Bash script that creates and moves the backup archive.
- `important-documents/` - Example directory containing files to back up.
- `important-documents.zip` - Compressed copy of the example documents.
- `backup-*.tar.gz` - Example backup archives produced by the script.
- `backup-script-copy` - A permissions and installation note for `/usr/local/bin/backup.sh`.

## Requirements

- Bash
- GNU `tar`
- GNU `date` with support for `date -r`

The script is intended for Linux, macOS, or a Unix-like environment such as Git Bash or WSL. On Windows, run it from Git Bash or WSL rather than from PowerShell.

## Run Manually

From the parent directory, provide the source directory first and the destination directory second:

```bash
cd First_Cron_Job
bash backup.sh important-documents .
```

Both paths must already exist. The script prints the selected directories and creates an archive named like:

```text
backup-1790003260.tar.gz
```

The number is the Unix timestamp from when the backup was created.

To inspect an archive without extracting it:

```bash
tar -tzf backup-1790003260.tar.gz
```

To extract an archive into a separate directory:

```bash
mkdir restored-documents
tar -xzf backup-1790003260.tar.gz -C restored-documents
```

## Schedule With Cron

Make the script executable and use an absolute path in the cron entry:

```bash
chmod +x /path/to/First_Cron_Job/backup.sh
```

For example, to run it every day at midnight and store the archive in the `backups` directory:

```cron
0 0 * * * /path/to/First_Cron_Job/backup.sh /path/to/First_Cron_Job/important-documents /path/to/First_Cron_Job/backups >> /path/to/First_Cron_Job/backup.log 2>&1
```

Create the destination directory before enabling the job:

```bash
mkdir -p /path/to/First_Cron_Job/backups
```

Edit the current user's crontab with:

```bash
crontab -e
```

## How It Works

1. Validates that exactly two directory paths were provided.
2. Records the current Unix timestamp.
3. Finds entries in the source directory modified within the previous 24 hours.
4. Compresses those entries into `backup-<timestamp>.tar.gz`.
5. Moves the archive into the destination directory.

The scan covers entries directly inside the source directory. It does not recursively search nested directories for independently modified files.

## Current Limitations

- If no entry was modified in the last 24 hours, `tar` receives an empty file list and no useful backup is created.
- File and directory names containing spaces or shell-special characters are not handled robustly by the current array expansion.
- Existing backup archives in the source directory are included when they are newer than 24 hours.
- The script does not delete old backups or enforce a retention policy.
- Cron jobs have a limited environment, so use absolute paths for the script, source directory, destination directory, and log file.
from datetime import datetime as dt
from pathlib import Path

log_file = Path(__file__).resolve().parent.parent / "coin_log_file.txt"

def logs(message):
    print("logs() called with:", message)
    timestamp_format = '%Y-%b-%d-%H:%M:%S'
    now = dt.now()
    timestamp = now.strftime(timestamp_format)
    print("Timestamp generated:", timestamp)
    with open(log_file, 'a') as f:
        f.write(timestamp + ',' + message + '\n')
    # print("Write completed")


# if __name__ == "__main__":
#     report = logs('Checking for log')
#     print(report)
    
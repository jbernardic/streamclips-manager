import sys
from time import sleep
from datetime import datetime


def main():
    if len(sys.argv) != 2:
        print("Usage: python streamclips_mock.py <streamer_id>")
        sys.exit(1)
    
    streamer_id = sys.argv[1]
    print(f"Starting stream clips process for streamer {streamer_id}")
    
    while True:
        print(f"Processing clips for streamer {streamer_id} at {datetime.now()}")
        sleep(1)


if __name__ == "__main__":
    main()
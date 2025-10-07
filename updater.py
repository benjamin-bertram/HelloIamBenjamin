#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime
import time
import random

# Configuration
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
MD_FILE = "README.md"
MAX_COMMITS_PER_DAY = 2
MIN_INTERVAL = 1800  # Minimum interval between commits (30 minutes in seconds)
MAX_INTERVAL = 7200  # Maximum interval between commits (2 hours in seconds)

def update_md_timestamp():
    file_path = os.path.join(REPO_PATH, MD_FILE)
    try:
        # Read existing content
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Update first line with current timestamp
        current_time = datetime.now().strftime("%d.%m.%Y, %H:%M")
        if lines:
            lines[0] = f"{current_time}\n"
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error modifying file: {e}")
        return False

def git_commit():
    try:
        os.chdir(REPO_PATH)
        
        # Git commands
        subprocess.run(["git", "add", MD_FILE], check=True)
        commit_message = f"Update timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        
        print(f"Successfully committed at {datetime.now()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")
        return False

def get_random_interval():
    # Returns a random interval between MIN_INTERVAL and MAX_INTERVAL
    return random.randint(MIN_INTERVAL, MAX_INTERVAL)

def main():
    while True:
        today = datetime.now().date()
        commits_today = 0
        
        while commits_today < MAX_COMMITS_PER_DAY:
            if update_md_timestamp() and git_commit():
                commits_today += 1
            
            # If we've reached max commits, wait until next day
            if commits_today == MAX_COMMITS_PER_DAY:
                # Calculate seconds until midnight
                now = datetime.now()
                midnight = datetime(now.year, now.month, now.day, 23, 59, 59)
                seconds_until_midnight = (midnight - now).total_seconds() + 1
                time.sleep(seconds_until_midnight)
                break
            
            # Wait for random interval before next commit
            sleep_time = get_random_interval()
            time.sleep(sleep_time)
            
            # Check if we've crossed into a new day
            if datetime.now().date() != today:
                today = datetime.now().date()
                commits_today = 0

if __name__ == "__main__":
    # Initial setup check
    if not os.path.exists(os.path.join(REPO_PATH, ".git")):
        print("Error: Not a git repository. Please initialize git in the specified path.")
        exit(1)
    if not os.path.exists(os.path.join(REPO_PATH, MD_FILE)):
        print("Error: README.md not found in the specified path.")
        exit(1)
    
    print(f"Starting auto-commit script for {REPO_PATH}")
    main()

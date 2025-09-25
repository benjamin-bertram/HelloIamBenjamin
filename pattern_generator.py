import datetime as mydate
import os
import random
import uuid
import time
import git

class PatternGenerator:
    def __init__(self):
        self.project_dir = os.path.realpath(os.path.dirname(__file__))
        self.repo = None
        self.remote_url = "https://github.com/theveloper-pl/Fake-Git-History.git" # This should be the user's repo
        self.repo_name = self.remote_url.split("/")[-1].split(".")[0]
        self.pattern_file = "pattern.txt"
        self.pattern = []
        self.min_commits_per_day = 1
        self.max_commits_per_day = 5 # A reasonable range for pattern commits

    def load_repo(self):
        try:
            print("[Info]: Loading git repository")
            self.repo = git.Repo(os.path.join(self.project_dir, self.repo_name))
            print("[Info]: Repo loaded")
        except git.exc.NoSuchPathError:
            print("[Error]: Repo not found. Creating new one from remote-url")
            os.mkdir(os.path.join(self.project_dir, self.repo_name))
            self.repo = git.Repo.clone_from(self.remote_url, os.path.join(self.project_dir, self.repo_name))

    def read_pattern(self):
        pattern_path = os.path.join(self.project_dir, self.pattern_file)
        if not os.path.exists(pattern_path):
            print(f"[Error]: Pattern file not found at {pattern_path}")
            return False
        with open(pattern_path, 'r') as f:
            lines = f.readlines()
            # Filter out lines that are just separators or empty
            self.pattern = [line.strip() for line in lines if '0' in line or '-' in line]
        print(f"[Info]: Loaded pattern: {self.pattern}")
        return True

    def execute_commit(self, year: int, month: int, day: int):
        action_date = str(mydate.date(year, month, day).strftime('%Y-%m-%d %H:%M:%S'))
        os.environ["GIT_AUTHOR_DATE"] = action_date
        os.environ["GIT_COMMITTER_DATE"] = action_date
        # Create a dummy file or modify an existing one to ensure a commit is registered
        dummy_file_path = os.path.join(self.repo.working_dir, "pattern_commit_log.txt")
        with open(dummy_file_path, 'a') as f:
            f.write(f"Commit on {action_date} with UUID: {uuid.uuid4()}\n")
        self.repo.index.add([dummy_file_path])
        self.repo.index.commit(message=f"Pattern commit: {uuid.uuid4()}")

    def git_push(self):
        try:
            origin = self.repo.remote(name='origin')
            origin.push()
            print("[Info]: Changes have been pushed!")
            return True
        except Exception as e:
            print(f'[Error]: Error occurred while pushing the code !:\n{e}')
            return False

    def generate_pattern_commits(self, start_date: mydate.date):
        if not self.pattern:
            print("[Error]: No pattern loaded. Please call read_pattern first.")
            return

        current_date = start_date
        pattern_height = len(self.pattern)
        pattern_width = len(self.pattern[0]) if pattern_height > 0 else 0

        if pattern_width == 0:
            print("[Error]: Pattern has no width. Check pattern.txt format.")
            return

        # Calculate the number of days to simulate based on the pattern width
        # Each character in a pattern line represents a day
        total_pattern_days = pattern_width

        # Find the starting point in the pattern based on the current date
        # We want to align the current date with the correct day in the pattern
        today = mydate.date.today()
        days_since_start = (today - start_date).days

        # Ensure we don't go past the pattern's width
        if days_since_start >= total_pattern_days:
            print("[Info]: Pattern generation for past dates is complete. Waiting for next day to apply pattern.")
            return

        # Determine the column in the pattern for today's date
        current_pattern_column = days_since_start % pattern_width

        print(f"[Info]: Starting pattern generation from {start_date}. Today is {today}.")
        print(f"[Info]: Current pattern column for today: {current_pattern_column}")

        # Iterate through the pattern for the current day (column)
        commits_today = 0
        for row in range(pattern_height):
            if self.pattern[row][current_pattern_column] == '0':
                num_commits = random.randint(self.min_commits_per_day, self.max_commits_per_day)
                print(f"[Info]: Committing {num_commits} times for {today.strftime('%Y-%m-%d')}")
                for _ in range(num_commits):
                    self.execute_commit(today.year, today.month, today.day)
                commits_today += num_commits
        
        if commits_today > 0:
            self.git_push()
        else:
            print(f"[Info]: No commits for {today.strftime('%Y-%m-%d')} based on pattern.")


    def run_daily_update(self):
        while True:
            today = mydate.date.today()
            print(f"[Info]: Running daily update for {today.strftime('%Y-%m-%d')}")
            
            # Get start date from user
            while True:
                try:
                    start_date_str = input("Enter the pattern start date in YYYY/MM/DD format: ")
                    start_date_parts = [int(x) for x in start_date_str.split("/")]
                    pattern_start_date = mydate.date(start_date_parts[0], start_date_parts[1], start_date_parts[2])
                    break
                except ValueError:
                    print("[Error]: Invalid date format. Please use YYYY/MM/DD.")

            self.generate_pattern_commits(pattern_start_date)

            # Calculate time until next midnight
            now = mydate.datetime.now()
            next_midnight = mydate.datetime(now.year, now.month, now.day) + mydate.timedelta(days=1)
            time_to_sleep = (next_midnight - now).total_seconds()
            
            print(f"[Info]: Next update at {next_midnight.strftime('%Y-%m-%d %H:%M:%S')}. Sleeping for {time_to_sleep:.0f} seconds.")
            time.sleep(time_to_sleep)

if __name__ == "__main__":
    generator = PatternGenerator()
    generator.load_repo()
    if generator.read_pattern():
        generator.run_daily_update()
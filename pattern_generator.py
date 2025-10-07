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
        self.remote_url = "https://github.com/benjamin-bertram/HelloIamBenjamin" # This should be the user's repo
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
            # Include all lines from pattern.txt, stripping whitespace
            self.pattern = [line.strip() for line in lines]
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

    def reset_pattern_commits(self):
        print("\n[WARNING]: You are about to reset your branch and force push to remote.")
        print("[WARNING]: This is a DESTRUCTIVE operation and will rewrite history.")
        print("[WARNING]: ONLY PROCEED IF YOU UNDERSTAND THE IMPLICATIONS AND ARE SURE.")
        confirm = input("Type 'yes' to confirm reset and force push: ")
        if confirm.lower() != 'yes':
            print("[Info]: Reset operation cancelled.")
            return False

        try:
            # Ensure the repository is clean before fetching
            if self.repo.is_dirty(untracked_files=True):
                print("[Info]: Discarding local changes and untracked files...")
                self.repo.git.reset('--hard')
                self.repo.git.clean('-fdx')
                print("[Info]: Local changes discarded.")

            print("[Info]: Fetching latest from remote...")
            fetch_output = self.repo.remotes.origin.fetch()
            print(f"[Debug]: Fetch output: {fetch_output}")

            current_branch = self.repo.active_branch
            remote_branch_ref = f'origin/{current_branch.name}'
            print(f"[Info]: Resetting local branch '{current_branch.name}' to remote's state ('{remote_branch_ref}')...")
            reset_output = self.repo.git.reset('--hard', remote_branch_ref)
            print(f"[Debug]: Reset output: {reset_output}")

            # Remove the pattern_commit_log.txt file if it exists
            dummy_file_path = os.path.join(self.repo.working_dir, "pattern_commit_log.txt")
            if os.path.exists(dummy_file_path):
                os.remove(dummy_file_path)
                print(f"[Info]: Removed '{dummy_file_path}'.")
            
            # Add and commit the removal of the dummy file if it was tracked
            if self.repo.index.diff(None) or self.repo.untracked_files:
                print("[Info]: Staging changes (if any) after file removal...")
                self.repo.git.add(A=True)
                if self.repo.index.diff("HEAD"): # Check if there are actual changes to commit
                    print("[Info]: Committing removal of dummy file...")
                    self.repo.index.commit(message="Clean up pattern_commit_log.txt")
                else:
                    print("[Info]: No changes to commit after dummy file removal.")

            print(f"[Info]: Force pushing to remote branch '{current_branch.name}'...")
            push_output = self.repo.git.push('--force', 'origin', current_branch.name)
            print(f"[Debug]: Push output: {push_output}")
            print("[Info]: Repository successfully reset to remote's state.")
            return True
        except Exception as e:
            print(f"[Error]: Failed to reset and force push: {e}")
            return False

    def generate_pattern_commits(self, start_date: mydate.date):
        if not self.pattern:
            print("[Error]: No pattern loaded. Please call read_pattern first.")
            return

        pattern_height = len(self.pattern)
        pattern_width = len(self.pattern[0]) if pattern_height > 0 else 0

        if pattern_width == 0:
            print("[Error]: Pattern has no width. Check pattern.txt format.")
            return

        today = mydate.date.today()
        current_date = start_date
        
        # Generate historical commits up to yesterday
        print(f"[Info]: Generating historical commits from {start_date} to {today - mydate.timedelta(days=1)}")
        while current_date < today:
            # Calculate weekday (Sunday=0, Monday=1, ..., Saturday=6)
            weekday = (current_date.weekday() + 1) % 7
            # Correct vertical flip: top line in pattern.txt is Saturday, bottom is Sunday
            display_row_index = pattern_height - 1 - weekday
            # Calculate week offset relative to the start date
            week_offset = (current_date - start_date).days // 7

            commits_for_day = 0
            if display_row_index >= 0 and display_row_index < pattern_height and week_offset < pattern_width:
                if self.pattern[display_row_index][week_offset] == '0':
                    num_commits = random.randint(self.min_commits_per_day, self.max_commits_per_day)
                    for _ in range(num_commits):
                        self.execute_commit(current_date.year, current_date.month, current_date.day)
                    commits_for_day += num_commits
            
            if commits_for_day > 0:
                print(f"[Info]: Committed {commits_for_day} times for {current_date.strftime('%Y-%m-%d')}")
            else:
                print(f"[Info]: No commits for {current_date.strftime('%Y-%m-%d')} based on pattern.")
            
            current_date += mydate.timedelta(days=1)
        
        # Push all historical commits at once
        if start_date < today: # Only push if there were historical commits to make
            self.git_push()
        
        print(f"[Info]: Historical pattern generation complete. Starting daily updates from {today}.")
        
        # Start daily updates
        while True:
            current_day_to_commit = mydate.date.today()
            # Calculate weekday (Sunday=0, Monday=1, ..., Saturday=6)
            weekday = (current_day_to_commit.weekday() + 1) % 7
            # Correct vertical flip: top line in pattern.txt is Saturday, bottom is Sunday
            display_row_index = pattern_height - 1 - weekday
            # Calculate week offset relative to the start date
            week_offset = (current_day_to_commit - start_date).days // 7

            commits_for_day = 0
            if display_row_index >= 0 and display_row_index < pattern_height and week_offset < pattern_width:
                if self.pattern[display_row_index][week_offset] == '0':
                    num_commits = random.randint(self.min_commits_per_day, self.max_commits_per_day)
                    for _ in range(num_commits):
                        self.execute_commit(current_day_to_commit.year, current_day_to_commit.month, current_day_to_commit.day)
                    commits_for_day += num_commits
            
            if commits_for_day > 0:
                print(f"[Info]: Committed {commits_for_day} times for {current_day_to_commit.strftime('%Y-%m-%d')}")
                self.git_push()
            else:
                print(f"[Info]: No commits for {current_day_to_commit.strftime('%Y-%m-%d')} based on pattern.")

            # Calculate time until next midnight
            now = mydate.datetime.now()
            next_midnight = mydate.datetime(now.year, now.month, now.day) + mydate.timedelta(days=1)
            time_to_sleep = (next_midnight - now).total_seconds()
            
            print(f"[Info]: Next update at {next_midnight.strftime('%Y-%m-%d %H:%M:%S')}. Sleeping for {time_to_sleep:.0f} seconds.")
            time.sleep(time_to_sleep)

    def run_script(self):
        self.load_repo()
        if not self.read_pattern():
            return

        reset_choice = input("Do you want to reset your repository to the remote's state before generating the pattern? (yes/no): ")
        if reset_choice.lower() == 'yes':
            if not self.reset_pattern_commits():
                print("[Error]: Failed to reset repository. Aborting pattern generation.")
                return

        while True:
            try:
                start_date_str = input("Enter the pattern start date in YYYY/MM/DD format: ")
                start_date_parts = [int(x) for x in start_date_str.split("/")]
                pattern_start_date = mydate.date(start_date_parts[0], start_date_parts[1], start_date_parts[2])
                break
            except ValueError:
                print("[Error]: Invalid date format. Please use YYYY/MM/DD.")
        
        self.generate_pattern_commits(pattern_start_date)


if __name__ == "__main__":
    generator = PatternGenerator()
    generator.run_script()
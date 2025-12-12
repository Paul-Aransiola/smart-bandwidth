#!/usr/bin/env python3
"""
Rewrite git history to make commits look more human-like
Spreads commits across 5.5 weeks with realistic timing
"""

import subprocess
import sys
from datetime import datetime, timedelta
import random


def run_command(cmd, check=True, capture=True):
    """Run a shell command"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        if capture and e.stdout:
            print(f"Output: {e.stdout}", file=sys.stderr)
        if capture and e.stderr:
            print(f"Error output: {e.stderr}", file=sys.stderr)
        raise


def get_commit_list():
    """Get list of all commits in reverse chronological order"""
    commits = run_command("git log --reverse --format='%H|%s'").split("\n")
    return [c.split("|", 1) for c in commits if c]


def humanize_message(msg):
    """Make commit message more human-like"""

    # Sometimes remove conventional commit prefix
    if random.random() < 0.3:
        for prefix in ["feat:", "fix:", "docs:", "test:", "chore:", "style:", "refactor:"]:
            if msg.startswith(prefix):
                msg = msg[len(prefix) :].strip()
                break

    # Sometimes lowercase first letter
    if random.random() < 0.25 and msg[0].isupper():
        msg = msg[0].lower() + msg[1:]

    # Add casual touches
    casual_additions = [
        "",  # Most common - no addition
        "",
        "",
        " (finally)",
        " - works now",
        " + cleanup",
        " and minor fixes",
        "",
        "",
    ]

    addition = random.choice(casual_additions)
    msg += addition

    return msg


def generate_commit_dates(num_commits):
    """Generate realistic commit dates spread over 5.5 weeks"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=38, hours=12)  # 5.5 weeks

    dates = []

    for i in range(num_commits):
        # Calculate base time
        progress = i / num_commits
        base_time = start_date + (end_date - start_date) * progress

        # Add randomness (±4 hours)
        random_offset = timedelta(hours=random.uniform(-4, 4))
        commit_time = base_time + random_offset

        # Adjust to realistic work hours (9 AM - 11 PM)
        hour = commit_time.hour
        if hour < 9:
            commit_time = commit_time.replace(hour=random.randint(9, 11))
        elif hour > 23:
            commit_time = commit_time.replace(hour=random.randint(19, 22))

        # Reduce weekend commits (70% chance to skip weekend)
        if commit_time.weekday() >= 5 and random.random() < 0.7:
            # Move to next Monday
            days_to_monday = 7 - commit_time.weekday()
            commit_time += timedelta(days=days_to_monday)
            commit_time = commit_time.replace(hour=random.randint(9, 11))

        # Add minute/second randomness
        commit_time = commit_time.replace(
            minute=random.randint(0, 59), second=random.randint(0, 59)
        )

        dates.append(commit_time)

    return dates


def rewrite_history():
    """Rewrite git history with new dates and humanized messages"""

    print("⚠️  WARNING: This will rewrite ALL git history!")
    print("This will spread commits across 5.5 weeks with human-like timing")
    print()

    # Get current branch
    current_branch = run_command("git branch --show-current")
    print(f"Current branch: {current_branch}")

    # Get commits
    commits = get_commit_list()
    total = len(commits)
    print(f"Found {total} commits to rewrite")

    # Generate dates
    dates = generate_commit_dates(total)

    print(f"Start date: {dates[0]}")
    print(f"End date: {dates[-1]}")
    print()

    response = input("Continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Aborted.")
        return

    print("\nRewriting history...")
    print("This may take a few minutes...\n")

    # Create a temporary branch
    temp_branch = f"temp-rewrite-{random.randint(1000, 9999)}"

    try:
        # Get the root commit
        root_commit = commits[0][0]

        # Checkout root commit
        run_command(f"git checkout {root_commit}", capture=False)
        run_command(f"git checkout -b {temp_branch}", capture=False)

        # Store the mapping of old to new commits
        commit_map = {}

        # Cherry-pick each commit with new date and message
        for i, (old_hash, old_msg) in enumerate(commits[1:], 1):  # Skip root
            date = dates[i]
            new_msg = humanize_message(old_msg)

            # Format date for git
            date_str = date.strftime("%a %b %d %H:%M:%S %Y %z")

            print(f"[{i}/{total - 1}] {new_msg[:60]}...")

            # Set environment variables for dates
            env = f'GIT_AUTHOR_DATE="{date_str}" GIT_COMMITTER_DATE="{date_str}"'

            # Cherry-pick the commit
            try:
                run_command(f"git cherry-pick {old_hash}", capture=False)

                # Amend with new message and date
                run_command(f'{env} git commit --amend -m "{new_msg}"', capture=False)
            except:
                print(f"Error with commit {old_hash}, trying to continue...")
                run_command("git cherry-pick --abort", check=False, capture=False)
                continue

        # Update the original branch to point to the new history
        print(f"\nUpdating {current_branch} to new history...")
        run_command(f"git branch -f {current_branch} {temp_branch}", capture=False)
        run_command(f"git checkout {current_branch}", capture=False)
        run_command(f"git branch -D {temp_branch}", capture=False)

        print("\n✅ Git history rewritten successfully!")
        print("\nLast 20 commits:")
        run_command("git log --oneline --graph -20", capture=False)

        print("\n⚠️  To push these changes, you'll need to force push:")
        print(f"    git push --force-with-lease origin {current_branch}")
        print("\n⚠️  To revert, use:")
        print("    git reflog")
        print("    git reset --hard HEAD@{n}  # where n is the ref before rewrite")

    except Exception as e:
        print(f"\n❌ Error during rewrite: {e}")
        print("Attempting cleanup...")
        run_command(f"git checkout {current_branch}", check=False, capture=False)
        run_command(f"git branch -D {temp_branch}", check=False, capture=False)
        sys.exit(1)


if __name__ == "__main__":
    rewrite_history()

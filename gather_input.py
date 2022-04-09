import subprocess as sp
import locale
import typing as tp
import sys
import pickle
from pathlib import Path

def git_log_output(commit_range: str) -> tp.List[str]:
    try:
        output = sp.run(f'git log {commit_range} --format="%p -> %h"', stdout=sp.PIPE, encoding=locale.getpreferredencoding())
    except FileNotFoundError as ex:
        print(f"Failed to do git log for '{commit_range}'")
        raise ex

    return output.stdout.split('\n')

class CommitRangeSecretary:
    def __init__(self):
        self.cache_filename = Path(__file__).resolve().parents[0] / "cache.pik"

    def parse_stdin(self) -> tp.List[str]:
        uniq_git_log_lines: str = []
        all_commit_ranges_seen_before = True
        for line in sys.stdin:
            log_output = git_log_output( line.strip() )

            if not uniq_git_log_lines:
                uniq_git_log_lines = log_output
                continue

            for item in log_output:
                if item not in uniq_git_log_lines:
                    uniq_git_log_lines.append(item)

        return uniq_git_log_lines

if __name__ == '__main__':
    se = CommitRangeSecretary()
    for line in se.parse_stdin():
        print(line)
    
import subprocess as sp
import locale
import typing as tp
import os
import sys
import pickle
from pathlib import Path
from enum import Enum

def git_log_output(commit_range: str) -> tp.List[str]:
    try:
        output = sp.run(f'git log {commit_range} --format="%p -> %h"', stdout=sp.PIPE, shell=True, encoding=locale.getpreferredencoding())
    except FileNotFoundError as ex:
        print(f"Failed to do git log for '{commit_range}'")
        raise ex

    return output.stdout.split('\n')

class CheckResult(Enum):
    HISTORY_FOLLOWED = 0
    HISTORY_DEFIED = 1
    BEYOND_HISTORY = 2

class LastSeenResults:
    def __init__(self):
        self.commit_ranges: tp.List[str] = []
        self.uniq_git_log_lines: tp.List[str] = []
        self.line_count = 0

    def next_line_follows_history(self, commit_range: str) -> CheckResult:
        if len(self.commit_ranges) <= self.line_count:
            return CheckResult.BEYOND_HISTORY

        if self.commit_ranges[self.line_count] == commit_range:
            self.line_count += 1
            return CheckResult.HISTORY_FOLLOWED

        self.commit_ranges = self.commit_ranges[:self.line_count]
        return CheckResult.HISTORY_DEFIED

class CommitRangeSecretary:
    def __init__(self):
        self.cache_filename = Path(__file__).resolve().parents[0] / "cache.pik"
        self.last_seen_results: LastSeenResults = None
        self._load_cache()

    def _load_cache(self) -> None:
        if not os.path.isfile(self.cache_filename):
            self.last_seen_results = LastSeenResults()
            return

        with open(self.cache_filename, 'rb') as inF:
            self.last_seen_results = pickle.load(inF)

    def _save_cache(self) -> None:
        self.last_seen_results.line_count = 0
        with open(self.cache_filename, 'wb') as outF:
            pickle.dump(self.last_seen_results, outF, pickle.HIGHEST_PROTOCOL)

    def parse_stdin(self) -> tp.List[str]:
        commit_ranges_seen: tp.List[str] = []
        all_commit_ranges_seen_before = True
        for line in sys.stdin:
            commit_range = line.strip()
            if not commit_range:
                continue
            commit_ranges_seen.append(commit_range)

            if all_commit_ranges_seen_before:
                res = self.last_seen_results.next_line_follows_history(commit_range)
                if res == CheckResult.HISTORY_DEFIED:
                    all_commit_ranges_seen_before = False

        uniq_git_log_lines: tp.List[str] = []
        if all_commit_ranges_seen_before:
            start_line = self.last_seen_results.line_count
            commit_ranges_to_scan = commit_ranges_seen[start_line:]
            uniq_git_log_lines = self.last_seen_results.uniq_git_log_lines
        else:
            commit_ranges_to_scan = commit_ranges_seen

        for commit_range in commit_ranges_to_scan:
            log_output = git_log_output(commit_range)

            if not uniq_git_log_lines:
                uniq_git_log_lines = log_output
                continue

            for item in log_output:
                if item not in uniq_git_log_lines:
                    uniq_git_log_lines.append(item)

        self.last_seen_results.uniq_git_log_lines = uniq_git_log_lines
        self.last_seen_results.commit_ranges = commit_ranges_seen
        self._save_cache()

        return uniq_git_log_lines

if __name__ == '__main__':
    se = CommitRangeSecretary()
    for line in se.parse_stdin():
        if line.strip():
            print(line)
    
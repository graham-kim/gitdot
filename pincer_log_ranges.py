import typing as tp
import argparse
import sys
from query_descendant import query_descendant

import os
from git import Repo

def setup_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('commits', nargs=2, help="Querying ancestor commit hash")
    return parser

def print_pincer_commit_ranges(commits):
    if query_descendant(commits[0], commits[1]) or query_descendant(commits[1], commits[0]):
        sys.stderr.write(f"Direct lineage detected between {commits}")
        return

    repo = Repo(os.getcwd())
    base = repo.git.merge_base(commits[0], commits[1])
    print(f"{base} -1")
    print(f"{base}..{commits[0]}")
    print(f"{base}..{commits[1]}")

if __name__ == '__main__':
    args = setup_argparse().parse_args()
    print_pincer_commit_ranges(args.commits)

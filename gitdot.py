#--format="%p -> %h"

import typing as tp
import os
import sys
from collections import namedtuple
from git import Repo
import re
import github as gh
import json
from pathlib import Path
from pr_secretary import PrSecretary

merge_pr_regex = re.compile(r"Merge pull request #(\d+) from \S+/(\S+)")
merge_local_branch_regex = re.compile(r"Merge branch '(\S+)' into (\S+)")
merge_remote_branch_regex = re.compile(r"Merge remote-tracking branch 'origin/(\S+)' into (\S+)")

cfg_filename = Path(__file__).resolve().parent / "branch_colours.json"
if os.path.isfile(cfg_filename):
    with open(cfg_filename, 'r') as inF:
        col_cfg = json.load(inF)
else:
    col_cfg = {
        "main": "red"
    }

class MergeInfo:
    def __init__(self):
        self.src: str = None
        self.dst: str = None
        self.summary: str = None



def parse_merge_message(summary: str, pr_secr: PrSecretary) -> MergeInfo:
    info = MergeInfo()
    m = merge_pr_regex.match(summary)
    if m:
        info.src = f'PR #{m.group(1)} {m.group(2)}'

        if pr_secr.can_look():
            sys.stderr.write(f"Looking up PR #{m.group(1)}\n")
            sys.stderr.flush()
            info.dst = pr_secr.lookup_dst_branch_name(int(m.group(1)))
        return info

    m = merge_local_branch_regex.match(summary)
    if not m:
        m = merge_remote_branch_regex.match(summary)
    if not m:
        info.summary = summary
        return info

    info.src = m.group(1)
    info.dst = m.group(2)
    return info

def describe_commit_in_dot(commit_hash: str, fillcolor: str = "yellow") -> str:
    line = f'    _{commit_hash}'
    if fillcolor:
        line += f' [fillcolor="{fillcolor}"]'
    return line

def describe_merge_commit_in_dot(repo: Repo, commit_hash: str, pr_secr: PrSecretary, \
                                 fillcolor: str = None) -> str:
    commit = repo.commit(commit_hash)
    info = parse_merge_message(str(commit.summary), pr_secr)

    if fillcolor is None:
        fillcolor = "yellow"
        if info.dst in col_cfg:
            fillcolor = col_cfg[info.dst]

    line = describe_commit_in_dot(commit_hash, fillcolor)
    line = line.strip(']') + f', label="{commit_hash}\\n'
    if info.summary is not None:
        line += info.summary
    else:
        line += f'src: {info.src}'
        if info.dst is not None:
            line += f'\\ndst: {info.dst}'
    line += '"]'

    return line

def translate_to_dot(parent: str, child: str, highlight_link: bool=False) -> str:
    ans = f"    _{parent} -> _{child}"
    if highlight_link:
        ans += ' [style="dashed, bold", color="red"]'
    return ans

class OneParentCommit:
    def __init__(self, commit_hash: str, first_child: str):
        self.hash = commit_hash
        self.child = [first_child]

    def add_child(self, child_hash: str):
        self.child.append(child_hash)

    def only_one_child(self) -> bool:
        return len(self.child) == 1

    def output_lines(self) -> tp.List[str]:
        return [translate_to_dot(self.hash, child_hash, True) for child_hash in self.child]

def condense_OPCs(one_parent_commits: tp.Dict[str, OneParentCommit]):
    for occ_hash in [k for k,v in one_parent_commits.items() if v.only_one_child()]:
        occ_child = one_parent_commits[occ_hash].child[0]
        if occ_child in one_parent_commits:
            takeover_target = one_parent_commits.pop(occ_child)
            takeover_target.hash = occ_hash
            one_parent_commits[occ_hash] = takeover_target

class ParseResults:
    def __init__(self):
        self.one_parent_commits: tp.Dict[str, OneParentCommit] = {}
        self.multi_parent_dot_lines: tp.List[str] = []
        self.multi_parent_nodes: tp.List[str] = []

def parse_stdin(repo: Repo, pr_secr: PrSecretary) -> ParseResults:
    results = ParseResults()
    for line in sys.stdin:
        if "->" not in line:
            raise Exception(f"Every line must contain '->', got:\n{line}")

        lhs_rhs = line.strip().split('->')
        if len(lhs_rhs) != 2:
            raise Exception("Every line must only contain one '->'")

        lhs, rhs = lhs_rhs
        if ' ' in rhs.strip():
            raise Exception("%p -> %h should have only one hash on the right")

        parents = lhs.strip().split(' ')
        child = rhs.strip()
        if len(parents) > 1:
            results.multi_parent_nodes.append( describe_merge_commit_in_dot(repo, child, pr_secr) )
            for p in parents:
                results.multi_parent_dot_lines.append( translate_to_dot(p, child) )
        else:
            parent = parents[0]
            if parent in results.one_parent_commits:
                results.one_parent_commits[parent].add_child(child)
            else:
                results.one_parent_commits[parent] = OneParentCommit(parent, child)
    condense_OPCs(results.one_parent_commits)
    return results

def connect_to_repo(access_token_env_var: str, repo_name_env_var: str) -> gh.Repository.Repository:
    access_token = os.environ[access_token_env_var]
    if not access_token:
        raise Exception(f"Must provide an access token in the environment variable {access_token_env_var}")

    repo_name = os.environ[repo_name_env_var]
    if not repo_name:
        raise Exception(f"Must provide a GitHub repo name in the environment variable {repo_name_env_var}")

    g = gh.Github(access_token)
    return g.get_repo(repo_name)

def print_dot(repo: Repo, pr_secr: PrSecretary):
    print("digraph {")
    print("    rankdir=TD")
    print('    node [shape="box", style="filled", fillcolor="white"]\n')
    results = parse_stdin(repo, pr_secr)
    for line in results.multi_parent_nodes:
        print(line)
    print("")
    for line in results.multi_parent_dot_lines:
        print(line)
    print("")
    for opc in results.one_parent_commits.values():
        for line in opc.output_lines():
            print(line)
    print("}")

if __name__ == '__main__':
    pr_secr = PrSecretary(connect_to_repo("GITHUB_ACCESS_TOKEN", "GITHUB_REPO_NAME"))
    print_dot(Repo(os.getcwd()), pr_secr)

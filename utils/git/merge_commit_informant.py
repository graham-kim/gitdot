import typing as tp
import os
import re
from git import Repo

from .pr_secretary import PrSecretary
from utils.printerr import printerr

merge_pr_regex = re.compile(r"Merge pull request #(\d+) from \S+/(\S+)")
merge_local_branch_regex = re.compile(r"Merge branch '(\S+)' into (\S+)")
merge_remote_branch_regex = re.compile(r"Merge remote-tracking branch 'origin/(\S+)' into (\S+)")

class MergeInfo:
    def __init__(self):
        self.src: str = None
        self.dst: str = None
        self.summary: str = None

class MergeInformant:
    def __init__(self, pr_secr: PrSecretary):
        self.repo = Repo(os.getcwd())
        self.pr_secr = pr_secr

    def parse_merge_message(self, commit_hash: str) -> MergeInfo:
        info = MergeInfo()

        commit = self.repo.commit(commit_hash)
        summary = str(commit.summary)

        m = merge_pr_regex.match(summary)
        if m:
            info.src = f'PR #{m.group(1)} {m.group(2)}'

            if self.pr_secr.can_look():
                #printerr(f"Looking up PR #{m.group(1)}")
                info.dst = self.pr_secr.lookup_dst_branch_name(int(m.group(1)))
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
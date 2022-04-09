import github as gh
import pickle
import typing as tp
import os
from pathlib import Path

class PrSecretary:
    def __init__(self, github_repo: gh.Repository.Repository = None):
        self.github_repo: gh.Repository.Repository = github_repo
        self.pr_num_dst_cache: tp.Dict[int, str] = {}
        self._load_cache()

    def _get_savefile_name(self) -> Path:
        filename = self.github_repo.name + ".pik"
        return Path(__file__).resolve().parents[0] / filename

    def _load_cache(self) -> None:
        savefile = self._get_savefile_name()
        if not os.path.isfile(savefile):
            return

        with open(savefile, 'rb') as inF:
            self.pr_num_dst_cache = pickle.load(inF)

    def save_cache(self) -> None:
        savefile = self._get_savefile_name()
        with open(savefile, 'wb') as outF:
            pickle.dump(self.pr_num_dst_cache, outF, pickle.HIGHEST_PROTOCOL)

    def can_look(self) -> bool:
        return self.github_repo is not None

    def lookup_dst_branch_name(self, pr_num: int) -> str:
        if pr_num not in self.pr_num_dst_cache:
            self.pr_num_dst_cache[pr_num] = self.github_repo.get_pull(pr_num).base.ref
        return self.pr_num_dst_cache[pr_num]

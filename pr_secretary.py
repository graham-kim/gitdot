import github as gh
import pickle
import typing as tp
import os
from pathlib import Path

from utils import printerr

class PrSecretary:
    def __init__(self, access_token_env_var: str, repo_name: str):
        self._connect_to_repo(access_token_env_var, repo_name)
        self.pr_num_dst_cache: tp.Dict[int, str] = {}
        self._load_cache()

    def _connect_to_repo(self, access_token_env_var: str, repo_name: str) -> None:
        access_token = os.environ[access_token_env_var]
        if not access_token:
            raise Exception(f"Must provide an access token in the environment variable {access_token_env_var}")

        g = gh.Github(access_token)
        self.github_repo = g.get_repo(repo_name)

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
            printerr(f"PR #{pr_num} not cached, querying GitHub")
            self.pr_num_dst_cache[pr_num] = self.github_repo.get_pull(pr_num).base.ref
        return self.pr_num_dst_cache[pr_num]

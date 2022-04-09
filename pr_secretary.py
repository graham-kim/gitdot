import github as gh

class PrSecretary:
    def __init__(self, github_repo: gh.Repository.Repository = None):
        self.github_repo: gh.Repository.Repository = github_repo

    def can_look(self) -> bool:
        return self.github_repo is not None

    def lookup_dst_branch_name(self, pr_num: int) -> str:
        return self.github_repo.get_pull(pr_num).base.ref

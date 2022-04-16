import typing as tp
import argparse
import os
from git import Repo

def setup_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--anc', help="Querying ancestor commit hash")
    parser.add_argument('--desc', help="Possible descendant commit hash")
    return parser

def query_descendant(anc: str, desc: str) -> bool:
    repo = Repo(os.getcwd())
    try:
        anc_commit = repo.commit(anc)
        desc_commit = repo.commit(desc)
    except gitdb.exc.BadName as ex:
        print(ex)
        return False

    return repo.is_ancestor(anc, desc)

if __name__ == '__main__':
    args = setup_argparse().parse_args()
    ans = "is" if query_descendant(args.anc, args.desc) \
          else "is not"
    print(f"{args.anc} {ans} an ancestor of {args.desc}")
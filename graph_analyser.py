#--format="%p -> %h"

import typing as tp

class ParsedLine:
    def __init__(self, line: str):
        if "->" not in line:
            raise Exception(f"Every line must contain '->', got:\n{line}")

        lhs_rhs = line.strip().split('->')
        if len(lhs_rhs) != 2:
            raise Exception("Every line must only contain one '->'")

        lhs, rhs = lhs_rhs
        if ' ' in rhs.strip():
            raise Exception("%p -> %h should have only one hash on the right")

        self.parents = lhs.strip().split(' ')
        self.child = rhs.strip()

    def is_multi_parent(self) -> bool:
        return len(self.parents) > 1

class OneParentCommit:
    def __init__(self, commit_hash: str, first_child: str):
        self.hash = commit_hash
        self.child = [first_child]

    def add_child(self, child_hash: str):
        self.child.append(child_hash)

    def only_one_child(self) -> bool:
        return len(self.child) == 1

class CommitLink:
    def __init__(self, parent_hash: str, commit_hash: str):
        self.parent_hash = parent_hash
        self.commit_hash = commit_hash

class GraphAnalyser:
    def __init__(self):
        self.one_parent_commits: tp.Dict[str, OneParentCommit] = {}
        self.merge_links: tp.List[CommitLink] = []
        self.multi_parent_nodes: tp.List[str] = []

    def process(self, lines: tp.List[ParsedLine]):
        for parsed_line in lines:
            if parsed_line.is_multi_parent():
                self.multi_parent_nodes.append(parsed_line.child)
                for p in parsed_line.parents:
                    self.merge_links.append( CommitLink(p, parsed_line.child) )
            else:
                parent = parsed_line.parents[0]
                if parent in self.one_parent_commits:
                    self.one_parent_commits[parent].add_child(parsed_line.child)
                else:
                    self.one_parent_commits[parent] = OneParentCommit(parent, parsed_line.child)
        self._condense_OPCs()

    def _condense_OPCs(self):
        for occ_hash in [k for k,v in self.one_parent_commits.items() if v.only_one_child()]:
            occ_child = self.one_parent_commits[occ_hash].child[0]
            if occ_child in self.one_parent_commits:
                takeover_target = self.one_parent_commits.pop(occ_child)
                takeover_target.hash = occ_hash
                self.one_parent_commits[occ_hash] = takeover_target

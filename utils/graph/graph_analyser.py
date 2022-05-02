#--format="%p -> %h"

import typing as tp
import networkx as nx

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
        self.parent = parent_hash
        self.child = commit_hash

    def is_equal(self, other_parent: str, other_child: str) -> bool:
        return self.parent == other_parent and self.child == other_child

class NodeToSquash:
    def __init__(self, parent_hash: str, own_hash: str, child_hash: str):
        self.parent = parent_hash
        self.own_hash = own_hash
        self.child = child_hash

class GraphAnalyser:
    def __init__(self, do_squash: bool=True):
        self.graph = nx.DiGraph()
        self.squashed_links: tp.List[CommitLink] = []
        self.merge_commits: tp.List[str] = []
        self.do_squash = do_squash

    def is_merge_commit(self, node) -> bool:
        return node in self.merge_commits

    def is_squashed_link(self, src_dst: tp.Tuple[str, str]) -> bool:
        if not self.do_squash:
            return False

        for link in self.squashed_links:
            if src_dst[0] == link.parent and src_dst[1] == link.child:
                return True
        return False

    def _get_parents_and_children(self, node) -> tp.Tuple[tp.List[str], tp.List[str]]:
        all_n = [x for x in nx.all_neighbors(self.graph, node)]
        child_n = [x for x in nx.neighbors(self.graph, node)]
        parent_n = [x for x in all_n if x not in child_n]
        return parent_n, child_n

    def _identify_merge_commits_and_squashable_nodes(self) -> tp.Dict[str, NodeToSquash]:
        ans: tp.Dict[str, NodeToSquash] = {}
        for node in self.graph.nodes:
            parent_n, child_n = self._get_parents_and_children(node)
            if len(parent_n) != 1:
                if len(parent_n) > 1:
                    self.merge_commits.append(node)
                continue
            if len(child_n) != 1:
                continue

            ans[node] = NodeToSquash(parent_n[0], node, child_n[0])

        return ans

    def _squash_nodes(self):
        nodes_to_squash = self._identify_merge_commits_and_squashable_nodes()
        while nodes_to_squash:
            node, info = nodes_to_squash.popitem()

            new_squash_link = CommitLink(info.parent, info.child)
            nodes_to_delete = [node]

            while new_squash_link.parent in nodes_to_squash:
                nodes_to_delete.append(new_squash_link.parent)

                info = nodes_to_squash.pop(new_squash_link.parent)
                new_squash_link.parent = info.parent

            while new_squash_link.child in nodes_to_squash:
                nodes_to_delete.append(new_squash_link.child)

                info = nodes_to_squash.pop(new_squash_link.child)
                new_squash_link.child = info.child

            self.squashed_links.append(new_squash_link)
            for item in nodes_to_delete:
                self.graph.remove_node(item)
            self.graph.add_edge(new_squash_link.parent, new_squash_link.child)

    def process(self, lines: tp.List[ParsedLine]):
        for parsed_line in lines:
            c = parsed_line.child
            for p in parsed_line.parents:
                self.graph.add_edge(p, c)
        if self.do_squash:
            self._squash_nodes()

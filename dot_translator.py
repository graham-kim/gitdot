#--format="%p -> %h"

import typing as tp
import os
import sys
import json

from pr_secretary import PrSecretary
from graph_analyser import ParsedLine, GraphAnalyser
from merge_commit_informant import MergeInfo, MergeInformant
from pathlib import Path

def describe_commit_in_dot(commit_hash: str, fillcolor: str = "yellow") -> str:
    line = f'    _{commit_hash}'
    if fillcolor:
        line += f' [fillcolor="{fillcolor}"]'
    return line

def describe_link_in_dot(parent: str, child: str, highlight_link: bool=False) -> str:
    ans = f"    _{parent} -> _{child}"
    if highlight_link:
        ans += ' [style="dashed, bold", color="red"]'
    return ans

class DotTranslator:
    def __init__(self, pr_secr: PrSecretary):
        self.graph_ana = GraphAnalyser()
        self.merge_inform = MergeInformant(pr_secr)

        self._load_branch_colour_config(Path(__file__).resolve().parent / "branch_colours.json")

    def _load_branch_colour_config(self, cfg_filename: Path):
        if os.path.isfile(cfg_filename):
            with open(cfg_filename, 'r') as inF:
                self.col_cfg = json.load(inF)
        else:
            self.col_cfg = {
                "main": "red"
            }

    def parse_stdin(self) -> None:
        lines: tp.List[ParsedLine] = []
        for line in sys.stdin:
            lines.append( ParsedLine(line) )

        self.graph_ana.process(lines)

    def describe_merge_commit_in_dot(self, commit_hash: str) -> str:
        info: MergeInfo = self.merge_inform.parse_merge_message(commit_hash)

        fillcolor = "yellow"
        if info.dst in self.col_cfg:
            fillcolor = self.col_cfg[info.dst]

        line: str = describe_commit_in_dot(commit_hash, fillcolor)

        line = line.strip(']') + f', label="{commit_hash}\\n'
        if info.summary is not None:
            line += info.summary
        else:
            line += f'src: {info.src}'
            if info.dst is not None:
                line += f'\\ndst: {info.dst}'
        line += '"]'

        return line

    def print_translation(self) -> None:
        print("digraph {")
        print("    rankdir=TD")
        print('    node [shape="box", style="filled", fillcolor="white"]\n')
        for node in self.graph_ana.multi_parent_nodes:
            line = self.describe_merge_commit_in_dot(node)
            print(line)
        print("")
        for item in self.graph_ana.merge_links:
            line = describe_link_in_dot(item.parent_hash, item.commit_hash)
            print(line)
        print("")
        for opc in self.graph_ana.one_parent_commits.values():
            for line in [describe_link_in_dot(opc.hash, child_hash, True) for child_hash in opc.child]:
                print(line)
        print("}")

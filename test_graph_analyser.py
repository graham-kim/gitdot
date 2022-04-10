import unittest
import typing as tp
import networkx as nx

from graph_analyser import ParsedLine, GraphAnalyser

def parse(lines: tp.List[str]):
    return [ParsedLine(line) for line in lines]

class TestGraphAnalyser(unittest.TestCase):
    def setUp(self) -> None:
        self.ga = GraphAnalyser()

    def test_collapse_long_chain(self) -> None:
        lines = [
            "A -> B",
            "B -> C",
            "C -> D",
            "D -> E"
        ]
        self.ga.process(parse(lines))

        self.assertEqual(1, len(self.ga.squashed_links), msg= \
            "Should have expected number of squashed links")
        self.assertEqual(2, len(self.ga.graph.nodes), msg= \
            "Should have expected number of nodes")
        self.assertTrue("A" in self.ga.graph.nodes, msg= \
            "Should have expected ancestor node")
        self.assertTrue("E" in self.ga.graph.nodes, msg= \
            "Should have expected descendant node")
        self.assertTrue(nx.is_path( self.ga.graph, ["A", "E"] ), msg= \
            "Should have expected connected path")

    def test_long_chain_with_forked_children(self) -> None:
        lines = [
            "A -> B",
            "B -> C",
            "C -> D",
            "D -> E",
            "C -> F"
        ]
        self.ga.process(parse(lines))

        self.assertTrue(nx.is_path( self.ga.graph, ["A", "C", "E"] ), msg= \
            "Should have expected connected path")
        self.assertTrue(nx.is_path( self.ga.graph, ["A", "C", "F"] ), msg= \
            "Should have expected connected path")
        self.assertFalse("B" in self.ga.graph.nodes, msg =\
            "Should have removed this node when squashing")
        self.assertFalse("D" in self.ga.graph.nodes, msg =\
            "Should have removed this node when squashing")

    def test_long_chain_with_merge_commit(self) -> None:
        lines = [
            "A -> B",
            "B -> C",
            "C -> D",
            "D -> E",
            "X -> D",
            "E -> F"
        ]
        self.ga.process(parse(lines))

        self.assertTrue(nx.is_path( self.ga.graph, ["A", "D", "F"] ), msg= \
            "Should have expected connected path")
        self.assertTrue(nx.is_path( self.ga.graph, ["X", "D", "F"] ), msg= \
            "Should have expected connected path")
        self.assertFalse("B" in self.ga.graph.nodes, msg =\
            "Should have removed this node when squashing")
        self.assertFalse("C" in self.ga.graph.nodes, msg =\
            "Should have removed this node when squashing")
        self.assertFalse("E" in self.ga.graph.nodes, msg =\
            "Should have removed this node when squashing")


if __name__ == '__main__':
    unittest.main()

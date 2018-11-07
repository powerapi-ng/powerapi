import pytest

from copy import deepcopy
from smartwatts.tree import Node


class TestNode():
    """
    Test smartwatts.tree.Node class
    """

    def test_add_child_depth1(self):
        """Test to add a leaf to a tree of depth 1"""

        root = Node('A')
        root.add_leaf(['A', 'B'], 1)
        assert len(root.childs) == 1
        assert root.childs[0] == Node('B', 1)

    def test_add_child_depth2(self):
        """Test to add a leaf to a tree of depth 2"""
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)

        assert len(root.childs) == 1

        node_b = root.childs[0]
        assert node_b.label == 'B'
        assert len(node_b.childs) == 1

        leaf = node_b.childs[0]
        assert leaf == Node('C', 1)

    def test_add_child_depth2_node_already_exist(self):
        """
        Test to add a leaf to a tree of depth 2 when its parent's node already
        exists
        """

        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        root.add_leaf(['A', 'B', 'D'], 2)

        assert len(root.childs) == 1

        node_b = root.childs[0]
        assert node_b.label == 'B'
        assert len(node_b.childs) == 2

        sorted_child = deepcopy(node_b.childs).sort(key=lambda node: node.label)
        leaf_c = sorted_child[0]
        assert leaf_c == Node('C', 1)
        leaf_d = sorted_child[0]
        assert leaf_d == Node('C', 1)

    def test_retrieve_leaf_value_depth1(self):
        """Test to retrieve the leaf added in test_add_child_depth1
        """
        root = Node('A')
        root.add_leaf(['A', 'B'], 1)

        assert root.retrieve_leaf_value(['A', 'B']) == [1]

    def test_retrieve_leaf_value_depth2(self):
        """Test to retrieve the leaf added in test_add_child_depth2
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)

        assert root.retrieve_leaf_value(['A', 'B', 'C']) == [1]

    def test_retrieve_2_leaf_value_depth2(self):
        """
        Test to retrieve the two leafs added in
        test_add_child_depth2_node_already_exist
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        root.add_leaf(['A', 'B', 'D'], 2)

        leafs = root.retrieve_leaf_value(['A', 'B'])
        leafs.sort()
        assert leafs == [1, 2]

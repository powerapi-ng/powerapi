# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest

from copy import deepcopy
from smartwatts.utils.tree import Node, Tree



class TestTree():
    """
    test smartwatts.tree.Tree class
    """

    def get_child_to_emtpy_tree(self):
        tree = Tree()

        assert tree.get(['A', 'B']) == []


    def test_add_child_to_empty_tree(self):
        tree = Tree()
        tree.add(['A', 'B'], 1)

        assert tree.root is not None
        assert len(tree.root.childs) == 1
        assert tree.root.label == 'A'
        assert tree.root.childs[0] == Node('B', 1)

    def test_get_from_root(self):
        tree = Tree()
        tree.add(['A', 'B'], 1)

        assert tree.get([]) == [1]
        assert tree.get(['A']) == [1]


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

        sorted_child = deepcopy(node_b.childs)
        sorted_child.sort(key=lambda node: node.label)
        leaf_c = sorted_child[0]
        assert leaf_c == Node('C', 1)
        leaf_d = sorted_child[0]
        assert leaf_d == Node('C', 1)

        
    def test_retrieve_leaf_value_depth1(self):
        """Test to retrieve the leaf added in test_add_child_depth1
        """
        root = Node('A')
        root.add_leaf(['A', 'B'], 1)

        assert root.retrieve_leaf_values(['A', 'B']) == [1]

    def test_retrieve_leaf_value_depth2(self):
        """Test to retrieve the leaf added in test_add_child_depth2
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)

        assert root.retrieve_leaf_values(['A', 'B', 'C']) == [1]

    def test_retrieve_2_leaf_value_depth2(self):
        """
        Test to retrieve the two leafs added in
        test_add_child_depth2_node_already_exist
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        root.add_leaf(['A', 'B', 'D'], 2)

        leafs = root.retrieve_leaf_values(['A', 'B'])
        leafs.sort()
        assert leafs == [1, 2]

    def test_retrieve_1_leaf_value_depth2_2_branch(self):
        """
        Test to retrieve the one leafs added in
        test_add_child_depth2_node_already_exist
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        root.add_leaf(['A', 'B', 'D'], 2)

        [leaf_c] = root.retrieve_leaf_values(['A', 'B', 'C'])
        assert leaf_c == 1

        [leaf_d] = root.retrieve_leaf_values(['A', 'B', 'D'])
        assert leaf_d == 2


    def test_get_childs_depth1(self):
        """Test to retrieve all childs and their path on test_add_child_depth1
        tree"""
        root = Node('A')
        root.add_leaf(['A', 'B'], 1)
        assert root.get_childs() == [(['A', 'B'], 1)]

    def test_get_childs_depth2(self):
        """Test to retrieve all childs and their path on test_add_child_depth2
        tree"""
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        assert root.get_childs() == [(['A', 'B', 'C'], 1)]

    def get_childs_depth1(self):
        """Test to retrieve all childs and their path on
        test_add_child_depth2_node_already_exist tree
        """
        root = Node('A')
        root.add_leaf(['A', 'B', 'C'], 1)
        root.add_leaf(['A', 'B', 'D'], 2)

        childs = root.get_childs()
        childs.sort()
        assert childs == [(['A', 'B', 'C'], 1), (['A', 'B', 'C'], 2)]

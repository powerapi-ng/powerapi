"""
module for using labeled tree data structure
"""
from copy import deepcopy
from functools import reduce


class Tree:
    """
    Encapsulate the tree data structure
    """

    def __init__(self):
        self.root = None

    def add(self, path, value):
        """add a leaf to the tree

        Parameters:
            path(list): path to the node, its length must be equal to the depth
                        of the tree and the last label of the path will be the
                        label of the leaf
            val: the value that will be stored in the leaf
        """
        if len(path) == 0:
            raise ValueError

        if self.root is None:
            self.root = Node(path[0])

        self.root.add_leaf(path, value)

    def get(self, path):
        """retrieves all leafs value under the node designating by path

        Parameters:
            path(list)

        Return (list): list of leafs value
        """
        return self.root.retrieve_leaf_values(path)


class Node:
    """A labeled tree data structure that store data in its leaf

    each node is labeled with a value a node can also be a leaf so it contains
    an other value and doesn't have child node

    leafs are stored at the same depth leaf can be retrieved by using the list
    of label from a root node to the leaf for example in the folowing tree
    (where node are labeled with a letter), we can access to Leaf5 with its path
    [A,C,H]

    all the leaf of the node can be retrieved by using the path to this node,
    for example to retrieve Leaf1 and Leaf2 we use the path [A,B]. To retrieve
    all the Leaf of the tree we use the path [A]

            __________Root:A _____
           |                      |
           |                      |
      __Node1:B __            _ Node2:C ____
     |            |          |      |       |
     |            |          |      |       |
    Leaf1:D   Leaf2:E   Leaf3:F   Leaf4:G   Leaf5:H

    Label could be any python value

    """

    def __init__(self, label, val=None):
        self.label = label
        self.is_leaf = (val is not None)

        self.childs = []
        self.val = val

    def add_leaf(self, path, val):
        """add a leaf to the tree

        create unexistant node between the root node and the new leaf

        Parameters:
            path(list): path to the node, its length must be equal to the depth
                        of the tree and the last label of the path will be the
                        label of the leaf
            val: the value that will be stored in the leaf
        """
        def aux(node, depth):
            label = path[depth]
            # if node is the leaf parent, create the leaf and add it to its
            # parent
            if depth == (len(path) - 1):
                node.childs.append(Node(label, val=val))
            # otherwise find the next node in the path and go down in the tree
            else:
                child_found = False
                for child in node.childs:
                    if child.label == label:
                        aux(child, depth + 1)
                        child_found = True
                        break
                # if no intermediate node, create it
                if not child_found:
                    child = Node(label)
                    node.childs.append(child)
                    aux(child, depth + 1)

        aux(self, 1)

    def retrieve_leaf_values(self, path):
        """retrieves all leafs value under the node designating by path

        Parameters:
            path(list)

        Return (list): list of leafs value
        """
        def aux(node, depth):
            label = path[depth]
            # if the current node is not in the path go back to the upper node
            if label != node.label:
                return []
            # if the current node is a leaf return its value
            if depth == (len(path) - 1):
                return node._get_leafs()

            # go down in all child nodes
            return reduce(lambda acc, child: acc + aux(child, depth + 1),
                          node.childs, [])
        return aux(self, 0)

    def _get_leafs(self):
        """retrives all leafs under this node"""
        if self.is_leaf:
            return [self.val]
        # concat all leafs value of the node's childs
        return reduce(lambda acc, child: acc + child._get_leafs(), self.childs,
                      [])

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        if (self.label != other.label or self.val != other.val or
            self.is_leaf != other.is_leaf):
            return False
        print('ok')
        sorted_child = deepcopy(self.childs)
        sorted_child.sort(key=lambda node: node.label)
        sorted_child2 = deepcopy(other.childs)
        sorted_child2.sort(key=lambda node: node.label)
        for node, other_node in zip(sorted_child, sorted_child2):
            if node != other_node:
                return False
        return True

"""
module for using labeled tree data structure
"""


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

    def add_child(self, path, val):
        """add a leaf to the tree

        Parameters:
            path(list): path to the node, its length must be equal to the depth
                        of the tree and the last label of the path will be the
                        label of the leaf
            val: the value that will be stored in the leaf
        """
        raise NotImplementedError

    def retrieve_leaf_values(self, path):
        """retrieves all leafs value under the node designating by path

        Parameters:
            path(list)

        Return (list): list of leafs value
        """
    raise NotImplementedError

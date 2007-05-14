# Author: Prabhu Ramachandran
# License: BSD style
# Copyright (c) 2004, Enthought, Inc.

"""Tests class_tree.py.  Uses the vtk module to test the code.  Also
tests if the tree generation works for the __builtin__ module.

"""

import unittest
from enthought.tvtk import class_tree

import vtk
import __builtin__

# This computation can be expensive, so we cache it.
_cache = class_tree.ClassTree(vtk)
_cache.create()


def get_level(klass):
    """Gets the inheritance level of a given class."""
    if not klass.__bases__:
        return 0
    else:
        return max([get_level(b) for b in klass.__bases__]) + 1


class TestClassTree(unittest.TestCase):
    def setUp(self):
        self.t = _cache
    
    def test_basic_vtk(self):
        """Basic tests for the VTK module."""
        t = self.t
        self.assertEqual(t.get_node('vtkObject').name, 'vtkObject')
        self.assertEqual(t.get_node('vtkObject').parents[0].name,
                         'vtkObjectBase')
        self.assertEqual(len(t.tree[0]), 1)
        self.assertEqual(t.tree[0][0].name, 'vtkObjectBase')

    def test_ancestors(self):
        """Check if get_ancestors is OK."""

        # The parent child information is already tested so this test
        # needs to ensure that the method works for a few known
        # examples.

        # Simple VTK test.
        t = self.t
        n = t.get_node('vtkDataArray')
        if hasattr(vtk, 'vtkAbstractArray'):
            self.assertEqual([x.name for x in n.get_ancestors()],
                             ['vtkAbstractArray', 'vtkObject', 'vtkObjectBase'])
        else:
            self.assertEqual([x.name for x in n.get_ancestors()],
                             ['vtkObject', 'vtkObjectBase'])

        # Simple __builtin__ test.
        t = class_tree.ClassTree(__builtin__)
        t.create()
        n = t.get_node('TabError')
        bases = ['IndentationError', 'SyntaxError',
                 'StandardError', 'Exception']
        if len(Exception.__bases__) > 0:
            bases.extend(['BaseException', 'object'])
        self.assertEqual([x.name for x in n.get_ancestors()],
                         bases)

    def test_parent_child(self):
        """Check if the node's parent and children are correct."""
        t = self.t

        for node in t:
            n_class = t.get_class(node.name)
            base_names = [x.__name__ for x in n_class.__bases__]
            base_names.sort()
            parent_names = [x.name for x in node.parents]
            parent_names.sort()
            self.assertEqual(base_names, parent_names)
            
            for c in node.children:
                c_class = t.get_class(c.name)
                base_names = [x.__name__ for x in c_class.__bases__]
                self.assertEqual(node.name in base_names, True)

    def test_level(self):
        """Check the node levels."""
        t = self.t
        for node in t:
            self.assertEqual(get_level(t.get_class(node.name)), node.level)

    def test_tree(self):
        """Check the tree structure."""
        t = self.t
        n = sum([len(x) for x in t.tree])
        self.assertEqual(n, len(t.nodes))

        for level, nodes in enumerate(t.tree):
            for n in nodes:
                self.assertEqual(n.level, level)

    def test_builtin(self):
        """Check if tree structure for __builtin__ works."""

        # This tests to see if the tree structure generation works for
        # the __builtin__ module.
        t = class_tree.ClassTree(__builtin__)
        t.create()
        self.t = t
        self.test_parent_child()
        self.test_level()
        self.test_tree()


def test_suite():
    suites = []
    suites.append(unittest.makeSuite(TestClassTree, 'test_'))
    total_suite = unittest.TestSuite(suites)
    return total_suite

def test(verbose=2):
    """Useful when you need to run the tests interactively."""
    all_tests = test_suite()
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(all_tests)
    return result, runner


if __name__ == "__main__":
    unittest.main()

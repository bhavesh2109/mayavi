"""
Tests for array_handler.py.
"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005, Enthought, Inc.
# License: BSD Style.

import unittest
import vtk

from enthought.util import numerix
from enthought.tvtk import array_handler
from test_tvtk_base import Prop
from enthought.tvtk import tvtk_base

def mysum(arr):
    val = arr
    while type(val) == numerix.ArrayType:
        val = numerix.sum(val)
    return val


class TestArrayHandler(unittest.TestCase):
    def _check_arrays(self, arr, vtk_arr):
        self.assertEqual(vtk_arr.GetNumberOfTuples(), len(arr))
        if len(arr.shape) == 2:
            dim1 = arr.shape[1]
            self.assertEqual(vtk_arr.GetNumberOfComponents(), dim1)
            for i in range(len(arr)):
                if dim1 in [1,2,3,4,9]:
                    res = getattr(vtk_arr, 'GetTuple%s'%dim1)(i)
                    self.assertEqual(numerix.sum(res - arr[i]), 0)
                else:
                    res = [vtk_arr.GetComponent(i, j) for j in range(dim1)]
                    self.assertEqual(numerix.sum(res - arr[i]), 0)
        else:
            if numerix.typecode(arr) == 'c':
                for i in range(len(arr)):
                    self.assertEqual(chr(int(vtk_arr.GetTuple1(i))), arr[i])
            else:
                for i in range(len(arr)):
                    self.assertEqual(vtk_arr.GetTuple1(i), arr[i])
        

    def test_array2vtk(self):
        """Test Numeric array to VTK array conversion and vice-versa."""
        # Put all the test arrays here.
        t_z = []        

        # Test the different types of arrays.
        t_z.append(numerix.array([-128, 0, 127], numerix.Int8))
        if numerix.which[0] == 'numeric':
            t_z.append(numerix.array([-128, 0, 127], numerix.Character))
        t_z.append(numerix.array([-32768, 0, 32767], numerix.Int16))
        t_z.append(numerix.array([-2147483648, 0, 2147483647], numerix.Int32))
        t_z.append(numerix.array([0, 255], numerix.UInt8))
        t_z.append(numerix.array([0, 65535], numerix.UInt16))
        t_z.append(numerix.array([0, 4294967295L], numerix.UInt32))
        t_z.append(numerix.array([-1.0e38, 0, 1.0e38], 'f'))
        t_z.append(numerix.array([-1.0e299, 0, 1.0e299], 'd'))

        # Check multi-component arrays.
        t_z.append(numerix.array([[1], [2], [300]], 'd'))
        t_z.append(numerix.array([[1, 20], [300, 4000]], 'd'))
        t_z.append(numerix.array([[1, 2, 3], [4, 5, 6]], 'f'))
        t_z.append(numerix.array([[1, 2, 3],[4, 5, 6]], 'd'))
        t_z.append(numerix.array([[1, 2, 3, 400],[4, 5, 6, 700]],
                                 'd'))
        t_z.append(numerix.array([range(9),range(10,19)], 'f'))

        # Test if a Python list also works.
        t_z.append(numerix.array([[1., 2., 3., 400.],[4, 5, 6, 700]],
                                 'd'))

        # Test if arrays with number of components not in [1,2,3,4,9] work.
        t_z.append(numerix.array([[1, 2, 3, 400, 5000],
                                  [4, 5, 6, 700, 8000]], 'd'))
        t_z.append(numerix.array([range(10), range(10,20)], 'd'))

        for z in t_z:
            vtk_arr = array_handler.array2vtk(z)
            # Test for memory leaks.
            self.assertEqual(vtk_arr.GetReferenceCount(), 2)
            #print z
            self._check_arrays(z, vtk_arr)
            z1 = array_handler.vtk2array(vtk_arr)
            if len(z.shape) == 1:
                self.assertEqual(len(z1.shape), 1)
            if numerix.typecode(z) != 'c':
                #print z1
                self.assertEqual(sum(numerix.ravel(z) - numerix.ravel(z1)), 0)
            else:
                #print z1.astype('c')
                self.assertEqual(z, z1.astype('c'))
        
        # Check if type conversion works correctly.
        z = numerix.array([-128, 0, 127], numerix.Int8)
        vtk_arr = vtk.vtkDoubleArray()
        ident = id(vtk_arr)
        vtk_arr = array_handler.array2vtk(z, vtk_arr)
        # Make sure this is the same array!
        self.assertEqual(ident, id(vtk_arr))
        self._check_arrays(z, vtk_arr)

        # Check the vtkBitArray.
        vtk_arr = vtk.vtkBitArray()
        vtk_arr.InsertNextValue(0)
        vtk_arr.InsertNextValue(1)
        vtk_arr.InsertNextValue(0)
        vtk_arr.InsertNextValue(1)
        arr = array_handler.vtk2array(vtk_arr)
        self.assertEqual(numerix.sum(arr - [0,1,0,1]), 0)
        vtk_arr = array_handler.array2vtk(arr, vtk_arr)
        self.assertEqual(vtk_arr.GetValue(0), 0)
        self.assertEqual(vtk_arr.GetValue(1), 1)
        self.assertEqual(vtk_arr.GetValue(2), 0)
        self.assertEqual(vtk_arr.GetValue(3), 1)

        # ----------------------------------------
        # Test if the array is copied or not.
        a = numerix.array([[1, 2, 3],[4, 5, 6]], 'd')
        vtk_arr = array_handler.array2vtk(a)
        # Change the numerix array and see if the changes are
        # reflected in the VTK array.
        a[0] = [10.0, 20.0, 30.0]
        self.assertEqual(vtk_arr.GetTuple3(0), (10., 20., 30.))

        # Make sure the cache is doing its job.
        key = vtk_arr.__this__
        z = array_handler._array_cache[key]
        self.assertEqual(numerix.sum(z - numerix.ravel(a)), 0.0)

        l1 = len(array_handler._array_cache)
        # del the Numeric array and see if this still works.
        del a
        self.assertEqual(vtk_arr.GetTuple3(0), (10., 20., 30.))
        # Check the cache -- just making sure.
        self.assertEqual(len(array_handler._array_cache), l1)

        # Delete the VTK array and see if the cache is cleared.
        del vtk_arr
        if numerix.which[0] != 'numpy':
            # FIXME: Somehow this does not work with numpy arrays.
            self.assertEqual(len(array_handler._array_cache), l1-1)
            self.assertEqual(array_handler._array_cache.has_key(key),
                             False)

        # Make sure bit arrays are copied.
        vtk_arr = vtk.vtkBitArray()
        a = numerix.array([0,1,0,1], numerix.Int32)
        vtk_arr = array_handler.array2vtk(a, vtk_arr)
        del a
        self.assertEqual(vtk_arr.GetValue(0), 0)
        self.assertEqual(vtk_arr.GetValue(1), 1)
        self.assertEqual(vtk_arr.GetValue(2), 0)
        self.assertEqual(vtk_arr.GetValue(3), 1)
        

    def test_arr2cell_array(self):
        """Test Numeric array to vtkCellArray conversion."""
        # Test list of lists.
        a = [[0], [1, 2], [3, 4, 5], [6, 7, 8, 9]]
        cells = array_handler.array2vtkCellArray(a)
        z = numerix.array([1, 0, 2, 1,2, 3, 3,4,5, 4, 6,7,8,9])
        arr = array_handler.vtk2array(cells.GetData())
        self.assertEqual(numerix.sum(arr - z), 0)
        self.assertEqual(len(arr.shape), 1)
        self.assertEqual(len(arr), 14)

        # Test if optional argument stuff also works.
        cells = vtk.vtkCellArray()
        ident = id(cells)
        cells = array_handler.array2vtkCellArray(a, cells)
        self.assertEqual(id(cells), ident)
        arr = array_handler.vtk2array(cells.GetData())
        self.assertEqual(numerix.sum(arr - z), 0)
        self.assertEqual(cells.GetNumberOfCells(), 4)

        # Make sure this resets the cell array and does not add to the
        # existing list!
        cells = array_handler.array2vtkCellArray(a, cells)
        self.assertEqual(cells.GetNumberOfCells(), 4)

        # Test Numeric array handling.
        N = 3
        a = numerix.zeros((N,3), numerix.Int)
        a[:,1] = 1
        a[:,2] = 2
        cells = array_handler.array2vtkCellArray(a)
        arr = array_handler.vtk2array(cells.GetData())
        expect = numerix.array([3, 0, 1, 2]*3,numerix.Int) 
        self.assertEqual(numerix.alltrue(numerix.equal(arr, expect)),
                         True)
        self.assertEqual(cells.GetNumberOfCells(), N)

        # Test if a list of Numeric arrays of different cell lengths works.
        l_a = [a[:,:1], a, a[:2,:2]]
        cells = array_handler.array2vtkCellArray(l_a)
        arr = array_handler.vtk2array(cells.GetData())
        expect = numerix.array([1, 0]*3 + [3, 0, 1, 2]*3 + [2, 0,1]*2,numerix.Int)
        self.assertEqual(numerix.alltrue(numerix.equal(arr, expect)),
                         True)
        self.assertEqual(cells.GetNumberOfCells(), N*2 + 2)

        # This should not take a long while.  This merely tests if a
        # million cells can be created rapidly.
        N = int(1e6)
        a = numerix.zeros((N,3), numerix.Int)
        a[:,1] = 1
        a[:,2] = 2
        cells = array_handler.array2vtkCellArray(a)
        self.assertEqual(cells.GetNumberOfCells(), N)

    def test_arr2vtkPoints(self):
        """Test Numeric array to vtkPoints conversion."""
        a = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
        p = array_handler.array2vtkPoints(a)
        self.assertEqual(p.GetPoint(0), (0.0, 0.0, 0.0))
        self.assertEqual(p.GetPoint(1), (1.0, 1.0, 1.0))
        p = vtk.vtkPoints()
        ident = id(p)
        p = array_handler.array2vtkPoints(numerix.array(a), p)
        self.assertEqual(p.GetPoint(0), (0.0, 0.0, 0.0))
        self.assertEqual(p.GetPoint(1), (1.0, 1.0, 1.0))
        self.assertEqual(id(p), ident)
        self.assertRaises(AssertionError, array_handler.array2vtkPoints,
                          [0.0, 1.0])
        self.assertRaises(AssertionError, array_handler.array2vtkPoints,
                          [0.0, 1.0, 1.0])
        

    def test_arr2vtkIdList(self):
        """Test array to vtkIdList conversion."""
        a = [1, 2, 3, 4, 5]
        p = array_handler.array2vtkIdList(a)
        for i, j in enumerate(a):            
            self.assertEqual(p.GetId(i), j)
        p = vtk.vtkIdList()
        ident = id(p)
        p = array_handler.array2vtkIdList(numerix.array(a), p)
        for i, j in enumerate(a):            
            self.assertEqual(p.GetId(i), j)
        self.assertEqual(id(p), ident)
        
        self.assertRaises(AssertionError, array_handler.array2vtkIdList,
                          [[1,2,3]])

    def test_get_correct_sig(self):
        """Test multiple signature cases that have array arguments."""
        obj = tvtk_base.TVTKBase(vtk.vtkIdTypeArray)
        sigs = [ None,
                 [['vtkDataArray']],
                 [['int', 'vtkIdList']],
                 [['int', 'vtkPoints'], ['int', 'int']],
                 [['int', 'vtkPoints'], ['int']],
                 [['int'], ['int', 'vtkPoints']],
                 [['int', 'vtkDataArray'], ['int', 'int']],
                 [['int', 'vtkDataArray'], ['int', 'int']],
                 [['vtkIdList', 'vtkCellArray'], ['int', 'vtkPoints'],
                  ['int', 'vtkDataArray']],
                 [['vtkIdList', 'vtkCellArray'], ['int', 'vtkPoints'],
                  ['int', 'vtkDataArray']],
                 [['vtkIdTypeArray', 'vtkCellArray'], ['int', 'vtkPoints'],
                  ['int', 'vtkDataArray']],
                 [['vtkIdTypeArray', 'vtkCellArray'], ['int', 'vtkPoints'],
                  ['int', 'vtkDataArray']],
                 [['vtkIdTypeArray', 'vtkCellArray'], ['int', 'vtkPoints'],
                  ['int', ('float', 'float', 'float')]],
                 ]
        args = [ [1], # No sig info.
                 ['foo'], # One sig.
                 [1], # One sig.
                 [1], # Error
                 [1], # Only one valid sig.
                 [1,[1,1,1]], # Only one valid sig.
                 [1, [1,1,1]], # Multiple valid sigs.
                 [1,1], # No arrays!
                 [1,1], # No match so returns None.
                 [1, [1,1,1]], # ambiguous, pick first match.
                 [numerix.array([1,1]), [1,1,1]], # Match!
                 [obj, [2,1,2,3]], # TVTK array object, match.
                 [[2,1,2,3], obj], # TVTK array object, match but has
                                   # wrong argument. Should be caught
                                   # by VTK.
                 ]
        res = [ None,
                ['vtkDataArray'],
                ['int', 'vtkIdList'],
                TypeError,
                ['int'],
                ['int', 'vtkPoints'],
                ['int', 'vtkDataArray'],
                None,
                None,
                ['int', 'vtkPoints'],
                ['vtkIdTypeArray', 'vtkCellArray'],
                ['vtkIdTypeArray', 'vtkCellArray'],
                ['vtkIdTypeArray', 'vtkCellArray'],
                ]
        for i in range(len(sigs)):
            if res[i] is TypeError:
                self.assertRaises(res[i], array_handler.get_correct_sig,
                                  args[i], sigs[i])
            else:
                s = array_handler.get_correct_sig(args[i], sigs[i])
                #print s, res[i]
                self.assertEqual(s, res[i])
            
    def test_deref_array(self):
        """Test if dereferencing array args works correctly."""
        sigs = [[['vtkDataArray']],
                [['vtkFloatArray']],
                [['vtkCellArray']],
                [['vtkPoints']],
                [['int', 'vtkIdList']],
                [['int', ('float', 'float'), 'vtkDataArray']],
                [['Prop', 'int', 'vtkDataArray']],
                [['Points', ('float', 'float', 'float')]]
                ]
        args = [[[1,2,3]],
                [[0,0,0]],
                [[[1,2,3],[4,5,6]]],
                [[[0.,0.,0.], [1.,1.,1.]]],
                [1, [1,2,3]],
                [1, (0.0, 0.0), [1.0, 1.0, 1.0]],
                [Prop(), 1, numerix.array([1.0, 1.0, 1.0])],
                [[[1,2,3]], [1,2,3]]
                ]
        r = array_handler.deref_array(args[0], sigs[0])
        self.assertEqual(mysum(array_handler.vtk2array(r[0]) -args[0]), 0)
        r = array_handler.deref_array(args[1], sigs[1])
        self.assertEqual(mysum(array_handler.vtk2array(r[0]) - args[1]), 0)

        r = array_handler.deref_array(args[2], sigs[2])
        self.assertEqual(r[0].GetNumberOfCells(), 2)
        
        r = array_handler.deref_array(args[3], sigs[3])
        self.assertEqual(mysum(array_handler.vtk2array(r[0].GetData()) -
                                     numerix.array(args[3], 'f')), 0)
        
        r = array_handler.deref_array(args[4], sigs[4])
        self.assertEqual(r[0], 1)
        self.assertEqual(r[1].__class__.__name__, 'vtkIdList')
                
        r = array_handler.deref_array(args[5], sigs[5])
        self.assertEqual(r[0], 1)
        self.assertEqual(r[1], (0.0, 0.0))
        self.assertEqual(mysum(array_handler.vtk2array(r[2]) -args[5][2]), 0)
        
        r = array_handler.deref_array(args[6], sigs[6])
        self.assertEqual(r[0].IsA('vtkProperty'), True)
        self.assertEqual(r[1], 1)
        self.assertEqual(mysum(array_handler.vtk2array(r[2]) -args[6][2]), 0)

        r = array_handler.deref_array(args[7], sigs[7])

    def test_reference_to_array(self):
        """Does to_array return an existing array instead of a new copy."""
        arr = numerix.arange(0.0, 10.0, 0.1)
        arr  = numerix.reshape(arr, (25, 4))
        vtk_arr = array_handler.array2vtk(arr)
        arr1 = array_handler.vtk2array(vtk_arr)
        # Now make sure these are using the same memory.
        arr[0][0] = 100.0
        self.assertEqual(arr[0][0], arr1[0][0])
        self.assertEqual(arr.shape, arr1.shape)
        

def test_suite():
    """Collects all the tests to be run."""
    suites = []
    suites.append(unittest.makeSuite(TestArrayHandler, 'test_'))
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
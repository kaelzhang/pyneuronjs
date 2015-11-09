import env
import unittest

from pyneuron import uniqueOrderedList 

class TestUniqueOrderedList(unittest.TestCase):

  def create_list(self):
    with self.assertRaises(TypeError):
      uniqueOrderedList(1)

    try:
      uniqueOrderedList()
      uniqueOrderedList([])
      uniqueOrderedList([1,2])
    except Exception, e:
      self.assertTrue(False)

  def test_isupper(self):
    self.assertTrue('FOO'.isupper())
    self.assertFalse('Foo'.isupper())

  def test_split(self):
      s = 'hello world'
      self.assertEqual(s.split(), ['hello', 'world'])
      # check that s.split fails when the separator is not a string
      with self.assertRaises(TypeError):
          s.split(2)

suite = unittest.TestLoader().loadTestsFromTestCase(TestUniqueOrderedList)
unittest.TextTestRunner(verbosity=2).run(suite)

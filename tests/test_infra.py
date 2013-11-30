import unittest
from constants import Point
from params import ALL_STANCES
import global_vars
from model.TrooperStance import TrooperStance
from tests.test_util import ContextFromFile
import util

class InfraTest(unittest.TestCase):

  def testDistances(self):
    _, _ = ContextFromFile('020_1_2_default')
    D = global_vars.distances
    self.assertEqual(29 + 19, D[0][0][29][19])
    self.assertEqual(19, D[0][0][0][19])
    self.assertEqual(7, D[1][4][1][9])
    self.assertEqual(8, D[1][4][1][10])
    self.assertEqual(8, D[1][10][1][4])
    self.assertEqual(0, D[1][4][1][4])
    self.assertEqual(10, D[16][11][13][8])
    self.assertEqual(10, D[13][8][16][11])
    self.assertEqual(12, D[13][11][16][18])
    self.assertEqual(12, D[16][18][13][11])
    self.assertEqual(None, D[16][17])

  def testVisibility(self):
    _, _ = ContextFromFile('040_2_2_map05')
    D = global_vars.cell_vision
    #self.assertEqual(D[TrooperStance.])

  def testIsVis(self):
    R = 7
    _, context = ContextFromFile('040_2_2_map05')
    for x in range(30):
      for y in range(20):
        if context.IsPassable(Point(x, y)):
          for x1 in range(30):
            for y1 in range(20):
              if context.IsPassable(Point(x1, y1)):
                for st in ALL_STANCES:
                  self.assertEqual(util.IsVisible(context, R, x, y, st, x1, y1, st),
                                   context.world.is_visible(R, x, y, st, x1, y1, st))


def testDominatedBy(self):
    _, context = ContextFromFile('040_2_2_map05')
    D = global_vars.cell_dominated_by
    self.assertTrue(Point(6, 18) not in D[TrooperStance.STANDING][6][0])

    self.assertTrue(Point(7, 1) in D[TrooperStance.STANDING][7][0])
    self.assertFalse(Point(7, 2) in D[TrooperStance.STANDING][7][0])
    self.assertTrue(Point(7, 5) in D[TrooperStance.STANDING][7][0])
    self.assertTrue(Point(7, 5) in D[TrooperStance.KNEELING][7][0])
    self.assertFalse(Point(7, 5) in D[TrooperStance.PRONE][7][0])

    self.assertTrue(Point(8, 2) in D[TrooperStance.PRONE][7][1])
    self.assertTrue(Point(8, 3) in D[TrooperStance.PRONE][7][1])
    self.assertFalse(Point(7, 1) in D[TrooperStance.PRONE][8][3])
    self.assertTrue(Point(8, 3) in D[TrooperStance.KNEELING][7][1])
    self.assertTrue(Point(7, 1) in D[TrooperStance.KNEELING][8][3])



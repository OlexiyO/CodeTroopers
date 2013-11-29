import unittest
from constants import Point
from model.ActionType import ActionType
from model.Move import Move
from tests.test_util import ContextFromFile


class BattleTest(unittest.TestCase):

  def testSniperLowerStance(self):
    strat, context = ContextFromFile('057_3_3_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.LOWER_STANCE)

  def testShootEnemy(self):
    strat, context = ContextFromFile('069_4_3_map02')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.SHOOT)
    self.assertEqual(move.x, 23)
    self.assertEqual(move.y, 10)

  def testNoExtraSteps(self):
    strat, context = ContextFromFile('058_2_1_map04')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 22)
    self.assertEqual(move.y, 6)

  def testShootOrLowerStance(self):
    # Lower stance -> shoot -> lower stance (hide)
    strat, context = ContextFromFile('022_1_2_map03')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.LOWER_STANCE)

    strat, context = ContextFromFile('023_1_2_map03')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.SHOOT)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 13)

  def testFighting(self):
    strat, context = ContextFromFile('040_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 6)

    strat, context = ContextFromFile('041_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 7)

    strat, context = ContextFromFile('042_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.EAT_FIELD_RATION)

    strat, context = ContextFromFile('043_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 8)

    strat, context = ContextFromFile('044_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.THROW_GRENADE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 13)


class ScoutingTest(unittest.TestCase):

  def testGo(self):
    strat, context = ContextFromFile('020_1_2_default')
    move = Move()
    print context.me.xy
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(Point(move.x, move.y), Point(25, 4))

  def testMustMedikit(self):
    strat, context = ContextFromFile('109_6_2_map04')
    move = Move()
    strat.RealMove(context, move)
    if move.action == ActionType.MOVE:
      self.assertEqual(move.action, ActionType.MOVE)
      self.assertEqual(Point(move.x, move.y), Point(21, 6))
    else:
      self.assertEqual(move.action, ActionType.USE_MEDIKIT)

  def testTakeMedikit(self):
    strat, context = ContextFromFile('049_2_3_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 23)
    self.assertEqual(move.y, 1)

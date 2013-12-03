import unittest
import actions
from constants import Point
import dfs
import global_vars
from model.ActionType import ActionType
from model.Move import Move
import scouting
from tests.test_util import ContextFromFile


class ReliabilityTest(unittest.TestCase):

  def testTimeout(self):
    strat, context = ContextFromFile('068_3_1_map05')
    move = Move()
    strat.RealMove(context, move)
    dfs.PrintDebugInfo()
    self.assertEqual(move.action, ActionType.USE_MEDIKIT)
    self.assertEqual(move.x, 21)
    self.assertEqual(move.y, 12)

  def testTimeout2(self):
    strat, context = ContextFromFile('040_2_3_default')
    move = Move()
    strat.RealMove(context, move)
    dfs.PrintDebugInfo()
    # Plan: walk to (2, 4), then throw grenade.
    # Can also plan B: walk to (1, 3), then (0, 3), then eat ration, then shoot and kill
    # but plan B is worse, because it spends ration, and ration is more useful to sniper.
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 2)
    self.assertEqual(move.y, 4)

  def testBreakDown(self):
    strat, context = ContextFromFile('533_24_3_default')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.END_TURN)


class BattleTest(unittest.TestCase):
  def testRunAwayFromUnknown(self):
    # In this case, we just got in touch with enemy -- and it makes sense to run away because it is too dangerous.
    strat, context = ContextFromFile('088_4_2_map04')
    move = Move()
    strat.RealMove(context, move)
    # Energizer, shoot, walk away
    self.assertEqual(move.action, ActionType.EAT_FIELD_RATION)

  def testSniperLowerStance(self):
    strat, context = ContextFromFile('057_3_3_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.LOWER_STANCE)

  def testHideDontFight(self):
    strat, context = ContextFromFile('142_6_2_cheeser')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.SHOOT)

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
    print global_vars.FORCED_ACTIONS
    print move.x, move.y
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 22)
    self.assertEqual(move.y, 6)

  def testShootOrLowerStance(self):
    # Lower stance -> shoot -> lower stance (hide)
    # Or: shoot, energy, shoot, walk away
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


class FightingTest(unittest.TestCase):
  def testFighting(self):
    strat, context = ContextFromFile('040_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    # The plan for real: step back to (24, 4) -- so the opponent can not see us; lower stance, shoot.
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 4)

  def testFighting2(self):
    strat, context = ContextFromFile('041_2_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 7)

  def testThrowGrenadeOptimally(self):
    """Now we see all opponents -- so we throw grenade to the crowd."""
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

  def testDontEatEnergizer(self):
    strat, context = ContextFromFile('004_0_3_map04')
    move = Move()
    plan = scouting.ScoutingMove(context, move)
    self.assertFalse(any(isinstance(x, actions.Energizer) for x in plan))

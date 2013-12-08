import unittest
import actions
from constants import Point
import dfs
import global_vars
from model.ActionType import ActionType
from model.Move import Move
from model.TrooperStance import TrooperStance
import scouting
from tests.test_util import ContextFromFile
import util


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

  def testRunTowardsEnemy(self):
    strat, context = ContextFromFile('065_3_2_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(Point(move.x, move.y), Point(23, 2))

  def testRunToProvideHelp(self):
    # Two guys are far away -- so they have to run to help the other 2.
    strat, context = ContextFromFile('016_0_3_map06')
    move = Move()
    plan = scouting.ScoutingMove(context, move)
    self.assertTrue(isinstance(plan[-1], actions.Walk))
    self.assertTrue(any(isinstance(x, actions.Walk) and x.where == Point(24, 1) for x in plan))

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

  def testLowerStance(self):
    # Bad: [Shoot {'where': Point(x=24, y=13)}, Energizer {}, Shoot {'where': Point(x=24, y=13)}, Walk {'where': Point(x=24, y=5)}]
    # Lower stance -> shoot -> lower stance (hide)
    # Or: shoot, energy, shoot, walk away
    strat, context = ContextFromFile('022_1_2_map03')
    move = Move()
    plan = strat.CombatMove(context, move)
    self.assertEqual(3, len(plan))
    self.assertEqual(move.action, ActionType.LOWER_STANCE)
    self.assertIsInstance(plan[1], actions.Shoot)
    self.assertEqual(plan[1].where, Point(24, 13))
    self.assertIsInstance(plan[2], actions.LowerStance)

    strat, context = ContextFromFile('023_1_2_map03')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.SHOOT)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 13)

  def testJustShoot(self):
    strat, context = ContextFromFile('207_12_2_map03')
    move = Move()
    plan = strat.RealMove(context, move)
    print plan
    self.assertEqual(move.action, ActionType.SHOOT)
    self.assertEqual(move.x, 17)
    self.assertEqual(move.y, 6)

  def testBeBrave(self):
    strat, context = ContextFromFile('308_15_2_map06')
    move = Move()
    global_vars.ALIVE_ENEMIES = [False, False, False, True, False]  # Only sniper
    enemy_xy = Point(13, 2)
    context.enemies[enemy_xy].hitpoints = 90
    plan = strat.RealMove(context, move)
    print plan
    self.assertEqual(move.action, ActionType.LOWER_STANCE)
    self.assertIsInstance(plan[1], actions.Shoot)
    self.assertEqual(plan[1].where, enemy_xy)


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
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(move.x, 24)
    self.assertEqual(move.y, 8)

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

  def testPickUpBonuses(self):
    strat, context = ContextFromFile('000_0_3_map06')
    move = Move()
    strat.Init(context)
    plan = strat.RealMove(context, move)
    self.assertTrue(any(isinstance(x, actions.Walk) and x.where in (Point(26, 3), Point(28, 0)) for x in plan))

  def testGo(self):
    strat, context = ContextFromFile('020_1_2_default')
    move = Move()
    print context.me.xy
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(Point(move.x, move.y), Point(26, 3))

  def testMustMedikit(self):
    strat, context = ContextFromFile('109_6_2_map04')
    move = Move()
    plan = scouting.ScoutingMove(context, move)
    self.assertTrue(any(isinstance(x, actions.UseMedikit) for x in plan))

  def testTakeMedikit(self):
    strat, context = ContextFromFile('049_2_3_map05')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)
    self.assertEqual(Point(move.x, move.y), Point(23, 1))

  def testDontEatEnergizer(self):
    strat, context = ContextFromFile('004_0_3_map04')
    move = Move()
    plan = scouting.ScoutingMove(context, move)
    self.assertFalse(any(isinstance(x, actions.Energizer) for x in plan))

  def testMoveSomewhere(self):
    global_vars.LAST_SEEN_ENEMIES = 8
    strat, context = ContextFromFile('140_10_0_map06')
    move = Move()
    strat.RealMove(context, move)
    self.assertEqual(move.action, ActionType.MOVE)

  def testDontStrayTooFar(self):
    strat, context = ContextFromFile('095_5_2_map06')
    global_vars.SetNextGoal(context, Point(6, 14))
    move = Move()
    plan = strat.RealMove(context, move)

    p = actions.Position(context)
    for a in plan:
      a.Apply(p)
    mx = max(util.ManhDist(p.me.xy, xy) for xy in context.allies)
    self.assertLessEqual(mx, 3)

  def testLayOnTheFloor(self):
    strat, context = ContextFromFile('624_22_1_map06')
    move = Move()
    global_vars.LAST_ENEMY_POSITION = [Point(15, 13)]
    plan = strat.RealMove(context, move)
    print plan

    p = actions.Position(context)
    for a in plan:
      a.Apply(p)
    self.assertLessEqual(p.me.stance, TrooperStance.PRONE)
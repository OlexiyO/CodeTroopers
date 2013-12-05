import cPickle as pickle
import os
from random import randint
import time
from actions import Position

import battle_evaluator
from constants import *
import constants

from context import Context
from dfs import BattleSearcher
import global_vars
import map_util
from model.ActionType import ActionType
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
import scouting
import util

BONUSES = {}
ENEMIES = {}
VISIBLE_CELLS = None
PREV_MOVE_INDEX = None
PREV_MOVE_TYPE = None
PREV_ACTION = None


def UnitsMoveInOrder(u1, u2, u3):
  assert u1 != u2, '%s != %s' % (u1, u2)
  assert u2 != u3, '%s != %s' % (u2, u3)
  assert u1 != u3, '%s != %s' % (u1, u3)
  assert len(global_vars.UNITS_ORDER) == global_vars.UNITS_IN_GAME
  n1 = global_vars.UNITS_ORDER.index(u1)
  n2 = global_vars.UNITS_ORDER.index(u2)
  n3 = global_vars.UNITS_ORDER.index(u3)
  if n1 < n3:
    return n1 < n2 < n3
  else:
    return n2 > n1 or n2 < n3


class MyStrategy(object):

  def Init(self, context):
    print map_util.HashOfMap(context)
    if global_vars.FIRST_MOVES_RANDOM > 0:
      print 'First %d moves at random!' % global_vars.FIRST_MOVES_RANDOM

    for ally in context.allies.itervalues():
      if ally.type == TrooperType.SNIPER:
        if ally.stance == TrooperStance.STANDING:
          assert ally.shooting_range == global_vars.SNIPER_SHOOTING_RANGE, (ally.shooting_range, global_vars.SNIPER_SHOOTING_RANGE)
    self.FillCornersOrder(context)
    p1, p2 = global_vars.ORDER_OF_CORNERS[0], global_vars.ORDER_OF_CORNERS[3]
    p3 = Point((p1.x*2 + p2.x) / 3, (p1.y*2 + p2.y) / 3)
    global_vars.NEXT_GOAL = ClosestEmptyCell(context, p3)
    print 'PPPP', p3, global_vars.NEXT_GOAL
    global_vars.UNITS_IN_GAME = len([t for t in context.world.troopers if t.teammate])
    if global_vars.STDOUT_LOGGING:
      print 'Start from', context.me.x, context.me.y

    t = time.time()
    util._PrecomputeDistances(context)
    util._FillCellImportance(context)
    print util.TOTAL_TIME
    dt = time.time() - t
    if global_vars.STDOUT_LOGGING:
      print 'Init in: %.2f' % dt
    global_vars.INITIALIZED = True

  def IsContinuingMove(self, context):
    global PREV_MOVE_INDEX
    global PREV_MOVE_TYPE
    return context.world.move_index == PREV_MOVE_INDEX and context.me.type == PREV_MOVE_TYPE
    
  def _PreMove(self, context):
    if context.me.type not in global_vars.UNITS_ORDER:
      assert context.world.move_index == 0, context.world.move_index
      global_vars.UNITS_ORDER.append(context.me.type)

    if not self.IsContinuingMove(context):
      global_vars.POSITION_AT_START_MOVE = context.me.xy
    # Update enemies.
    self._MergeEnemiesInfo(context)
    self._MergeBonusesInfo(context)
    self._MergeVisibleCells(context)

  def _MergeVisibleCells(self, context):
    global VISIBLE_CELLS
    if self.IsContinuingMove(context):
      context.MergeVisibleCells(VISIBLE_CELLS)
    VISIBLE_CELLS = context.visible_cells

  def _MergeBonusesInfo(self, context):
    # TODO: Remember places with possible bonuses. Visit them.
    global BONUSES
    if self.IsContinuingMove(context):
      res = {p: b for p, b in BONUSES.iteritems() if p != context.me.xy}
    else:
      res = {}

    for xy, bonus in context.bonuses.iteritems():
      res[xy] = bonus
    context.bonuses = res
    BONUSES = res

  def _MergeEnemiesInfo(self, context):
    # TODO: Don't drop enemies between turns.
    global ENEMIES
    global PREV_ACTION
    if self.IsContinuingMove(context):
      res = ENEMIES
    elif context.me.type != PREV_MOVE_TYPE:
      def CanSeeHim(enemy):
        # If I can see him, he'll be in the context.enemies list.
        return any(util.CanSee(context, ally, enemy) for ally in context.allies.itervalues())
      res = dict([(p, enemy) for p, enemy in ENEMIES.iteritems()
                  if (enemy.type != context.me.type and
                      enemy.type != PREV_MOVE_TYPE and
                      not CanSeeHim(enemy) and
                      # len(UNITS_ORDER) < TOTAL_UNITS means this is very first move.
                      (len(global_vars.UNITS_ORDER) < global_vars.UNITS_IN_GAME or not UnitsMoveInOrder(PREV_MOVE_TYPE, enemy.type, context.me.type)))])
    else:
      # Only one unit left. Everyone had a chance to move.
      res = {}

    for xy, enemy in context.enemies.iteritems():
      res[xy] = enemy
    context.enemies = res
    ENEMIES = res
    global_vars.UpdateSeenEnemies(context)

  def AdjustEnemiesToDmg(self, xy, dmg):
    global ENEMIES
    if xy in ENEMIES:
      if dmg > ENEMIES[xy].hitpoints:
        del ENEMIES[xy]
      else:
        ENEMIES[xy].hitpoints -= dmg

  def _PostMove(self, context, move):
    xy = Point(move.x, move.y)
    if move.action == ActionType.SHOOT:
      dmg = util.ShootDamage(context.me)
      self.AdjustEnemiesToDmg(xy, dmg)
    elif move.action == ActionType.THROW_GRENADE:
      dmg = context.game.grenade_direct_damage
      self.AdjustEnemiesToDmg(xy, dmg)
      for d in ALL_DIRS:
        p1 = PointAndDir(xy, d)
        self.AdjustEnemiesToDmg(xy, context.game.grenade_collateral_damage)

  def MaybeSaveLog(self, context):
    if constants.LOG_DIR is None:
      return
    cv = context.world.cell_visibilities
    if global_vars.TURN_INDEX == 0:
      cv_file = os.path.join(constants.LOG_DIR, 'visibilities')
      with open(cv_file, 'w') as cv_file:
        pickle.dump(cv, cv_file)
    context.world.cell_visibilities = None
    log_file = os.path.join(constants.LOG_DIR, '%03d_%s_%s.pickle' % (global_vars.TURN_INDEX, context.world.move_index, context.me.type))
    with open(log_file, 'w') as fout:
      pickle.dump(context, fout)
    context.world.cell_visibilities = cv

  def ReactAtPass(self, context, move):
    me = context.me
    if me.action_points >= me.shoot_cost:
      # We already made some moves. If there is still energy -- lets randomly shoot in any direction.
      my_shooting_range = util.ShootingRange(context, me)
      def ShootInvisible(where):
        if where in context.allies:
          return False
        for p in context.allies.itervalues():
          discount = 0 if p.type == TrooperType.SCOUT else context.game.sniper_prone_stealth_bonus
          sniper_vision_range = p.vision_range - discount
          if util.IsVisible(context, sniper_vision_range, p.x, p.y, p.stance, where.x, where.y, TrooperStance.PRONE):
            return False
        return util.IsVisible(context, my_shooting_range, me.x, me.y, me.stance,
                              where.x, where.y, TrooperStance.PRONE)

      bd = -1000
      for x in range(int(me.x - my_shooting_range), int(me.x + my_shooting_range + 1.01)):
        for y in range(int(me.y - my_shooting_range), int(me.y + my_shooting_range + 1.01)):
          where = Point(x, y)
          if context.IsPassable(where):
            value = global_vars.cell_vision[TrooperStance.PRONE][x][y] - len(global_vars.cell_dominated_by[TrooperStance.PRONE][x][y])
            if value > bd and ShootInvisible(where):
              move.action = ActionType.SHOOT
              move.x, move.y = x, y
              bd = value

  @util.TimeMe
  def move(self, me, world, game, move):
    context = Context(me, world, game)
    if not global_vars.INITIALIZED:
      self.Init(context)
    self.MaybeSaveLog(context)
    self._PreMove(context)
    move.action = ActionType.END_TURN
    self.RealMove(context, move)
    self._PostMove(context, move)
    if move.action == ActionType.END_TURN:
      self.ReactAtPass(context, move)

    if global_vars.STDOUT_LOGGING:
      unit_type = util.GetName(TrooperType, me.type)
      my_stance = util.GetName(TrooperStance, me.stance)
      action_name = util.GetName(ActionType, move.action)
      move_desc = ('(%2d, %2d)' % (move.x, move.y)) if move.x != -1 else ''
      print ('Move %d: %11s@(%2d, %2d) %s (%2d ap)'
             % (world.move_index, unit_type, me.xy.x, me.xy.y, my_stance, me.action_points) + ':       %s -> %s' % (action_name, move_desc))
      if global_vars.AT_HOME:
        if move.action == ActionType.MOVE and me.action_points < util.MoveCost(context, me.stance):
          print 'Please check bug at C:/Coding/CodeTroopers/bad_context.pickle'
          with open('C:/Coding/CodeTroopers/bad_context.pickle', 'w') as fout:
            pickle.dump(context, fout)
          assert False
    global PREV_MOVE_TYPE
    global PREV_MOVE_INDEX
    global PREV_ACTION
    PREV_MOVE_TYPE = me.type
    PREV_MOVE_INDEX = world.move_index
    PREV_ACTION = move.action
    global_vars.TURN_INDEX += 1

  def CombatMove(self, context, move):
    print 'Battle! Enemies:', context.enemies
    searcher = BattleSearcher()
    return searcher.DoSearch(battle_evaluator.EvaluatePosition, context, move)

  def RealMove(self, context, move):
    if global_vars.FIRST_MOVES_RANDOM > context.world.move_index:
      '''  # TODO: Change this when this strategy is used as old.
      for d in range(20):
        d1 = ALL_DIRS[d % 4]
        p1 = PointAndDir(context.me.xy, d1)
        if context.CanMoveTo(p1) and randint(0, 4) == 0:
          move.action = ActionType.MOVE
          move.x, move.y = p1.x, p1.y
          return
      '''
      return None

    if global_vars.FORCED_ACTIONS and (context.world.move_index, context.me.type) == global_vars.FORCED_MOVE_ID:
      print 'Using pre-computed action!'
      act = global_vars.FORCED_ACTIONS[0]
      global_vars.FORCED_ACTIONS = global_vars.FORCED_ACTIONS[1:]
      pos = Position(context)
      act.SetMove(pos, move)
      return global_vars.FORCED_ACTIONS
    global_vars.FORCED_ACTIONS = []
    global_vars.MOVE_INDEX = None
    if context.enemies:
      import time
      t0 = time.time()
      plan = self.CombatMove(context, move)
      t1 = time.time()
      util.MOVE_TIMES[context.world.move_index] = util.MOVE_TIMES.get(context.world.move_index, 0) + (t1 - t0)
      return plan
    else:
      return scouting.ScoutingMove(context, move)

  def FillCornersOrder(self, context):
    """Finds another corner to run to at the start of the game (second closest corner to this trooper)."""
    me = context.me
    global_vars.ORDER_OF_CORNERS = []
    x = 0 if me.x < X / 2 else X - 1
    y = 0 if me.y < Y / 2 else Y - 1
    global_vars.ORDER_OF_CORNERS.append(ClosestEmptyCell(context, Point(x, y)))
    y = 0 if y > Y / 2 else Y - 1  # Switch y
    global_vars.ORDER_OF_CORNERS.append(ClosestEmptyCell(context, Point(x, y)))
    x = 0 if me.x > X / 2 else X - 1
    global_vars.ORDER_OF_CORNERS.append(ClosestEmptyCell(context, Point(x, y)))
    y = 0 if y > Y / 2 else Y - 1  # Switch y
    global_vars.ORDER_OF_CORNERS.append(ClosestEmptyCell(context, Point(x, y)))
    global_vars.NEXT_CORNER = global_vars.ITERATION_ORDER


def ClosestEmptyCell(context, to):
  for dist in range(1, 10):
    for dx in range(dist + 1):
      for dy in range(dist + 1 - dx):
        for x in (-dx, dx):
          for y in (-dy, dy):
            p1 = Point(to.x + x, to.y + y)
            if context.CanMoveTo(p1):
              return p1
  return None

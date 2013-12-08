import cPickle as pickle
import collections
from copy import deepcopy
import os
import time
from actions import Position
import actions

import battle_evaluator
from constants import *
import constants

from context import Context
from dfs import BattleSearcher
import global_vars
from global_vars import PlayerOrder
import map_util
from model.ActionType import ActionType
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
import params
import scouting
import util

BONUSES = {}
ENEMIES = {}

VISIBLE_CELLS = None
KILLED = set()
# TODO: Change to use PREV_MOVE_ID
PREV_MOVE_INDEX = None
PREV_MOVE_TYPE = None
PREV_ACTION = None
PREV_XY = None


UnitID = collections.namedtuple('UnitID', ['player_id', 'unit_type'])
MoveID = collections.namedtuple('MoveID', ['move_index', 'unit_type'])

def UID(unit):
  return UnitID(unit.player_id, unit.type)


# To detect which player moves first.
# Ids are "who did we see" (UnitID). Values are where and when did we see them: (xy, MoveID)
ENEMIES_SEEN_LAST_TURN = {}
ALLIES_HISTORY = {}
ENEMIES_HISTORY = {}
LAST_NON_CONT_MOVE = None


def VisibleBySomeone(context, allies, enemy):
  return any(util.CanSee(context, ally, enemy) for ally in allies)


def SmthChanged(old_enemy, new_enemy):
  return (old_enemy.xy != new_enemy.xy or
          old_enemy.stance != new_enemy.stance or
          old_enemy.holding_grenade != new_enemy.holding_grenade or
          old_enemy.holding_medikit != new_enemy.holding_medikit or
          old_enemy.holding_field_ration != new_enemy.holding_field_ration)


def UnitsMoved(context):
  global ALLIES_HISTORY, ENEMIES_HISTORY, LAST_NON_CONT_MOVE, KILLED
  if LAST_NON_CONT_MOVE.move_index is None:
    # Very first move
    return
  old_allies = ALLIES_HISTORY[LAST_NON_CONT_MOVE]
  new_allies = context.allies.values()
  old_enemies = ENEMIES_HISTORY[LAST_NON_CONT_MOVE]
  new_enemies = {UID(enemy): enemy for enemy in context.enemies.itervalues()}
  all_enemies = set(old_enemies.keys() + new_enemies.keys())
  for unit_id in all_enemies:
    old_enemy = old_enemies.get(unit_id, None)
    new_enemy = new_enemies.get(unit_id, None)
    if old_enemy is not None and new_enemy is not None:
      if SmthChanged(old_enemy, new_enemy):
        yield unit_id, 2
    elif old_enemy is None:
      assert new_enemy is not None
      if VisibleBySomeone(context, old_allies, new_enemy):
        yield unit_id, 2
    else:
      assert new_enemy is None
      assert old_enemy is not None
      if unit_id not in KILLED and VisibleBySomeone(context, new_allies, old_enemy):
        yield unit_id, 1


def _CheckPlayersOrder(context):
  global ALLIES_HISTORY, ENEMIES_HISTORY, PREV_MOVE_INDEX, PREV_MOVE_TYPE, LAST_NON_CONT_MOVE
  current_move_id = MoveID(context.world.move_index, context.me.type)
  if IsContinuingMove(context):
    ALLIES_HISTORY[current_move_id].append(deepcopy(context.me))
    for enemy in context.enemies.itervalues():
      ENEMIES_HISTORY[current_move_id][UID(enemy)] = deepcopy(enemy)
  else:
    ALLIES_HISTORY[current_move_id] = [deepcopy(ally) for ally in context.allies.itervalues()]
    LAST_NON_CONT_MOVE = MoveID(PREV_MOVE_INDEX, PREV_MOVE_TYPE)
    ENEMIES_HISTORY[current_move_id] = {UID(enemy): deepcopy(enemy) for enemy in context.enemies.itervalues()}

  if context.me.type == LAST_NON_CONT_MOVE.unit_type:
    # Only one unit left. Anyone could have moved.
    return

  # TODO: Account for guys which were seen before last move.
  for unit_id, confidence in UnitsMoved(context):
    if unit_id.unit_type == context.me.type:
      global_vars.SetPlayerOrder(unit_id.player_id, PlayerOrder.BEFORE_ME, confidence)
    elif unit_id.unit_type == LAST_NON_CONT_MOVE.unit_type:
      global_vars.SetPlayerOrder(unit_id.player_id, PlayerOrder.AFTER_ME, confidence)



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


def IsContinuingMove(context):
  global PREV_MOVE_INDEX, PREV_MOVE_TYPE
  return context.world.move_index == PREV_MOVE_INDEX and context.me.type == PREV_MOVE_TYPE


class MyStrategy(object):

  def Init(self, context):
    print 'Players'
    for player in context.world.players:
      print 'Players', player.id, player.name
    print map_util.HashOfMap(context)
    if global_vars.FIRST_MOVES_RANDOM > 0:
      print 'First %d moves at random!' % global_vars.FIRST_MOVES_RANDOM

    for ally in context.allies.itervalues():
      if ally.type == TrooperType.SNIPER:
        if ally.stance == TrooperStance.STANDING:
          assert ally.shooting_range == global_vars.SNIPER_SHOOTING_RANGE, (ally.shooting_range, global_vars.SNIPER_SHOOTING_RANGE)
    self.FillCornersOrder(context)
    if map_util.MapName(context) == 'fefer':
      p3 = Point(X / 2, Y / 2)
    else:
      p1, p2 = global_vars.ORDER_OF_CORNERS[0], global_vars.ORDER_OF_CORNERS[3]
      p3 = Point((p1.x*2 + p2.x) / 3, (p1.y*2 + p2.y) / 3)
    global_vars.SetNextGoal(context, util.ClosestEmptyCell(context, p3))
    global_vars.UNITS_IN_GAME = len([t for t in context.world.troopers if t.teammate])
    global_vars.ORDER_OF_PLAYERS = {player.id: global_vars.PlayerOrder.UNKNOWN for player in context.world.players}
    global_vars.CONFIDENCE_ORDER = {player.id: 0 for player in context.world.players}
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

  def _PreMove(self, context):
    if context.me.type not in global_vars.UNITS_ORDER:
      assert context.world.move_index == 0, context.world.move_index
      global_vars.UNITS_ORDER.append(context.me.type)

    if not IsContinuingMove(context):
      global_vars.POSITION_AT_START_MOVE = context.me.xy
    # Check players order BEFORE updating enemies.
    _CheckPlayersOrder(context)
    # Update enemies.
    self._MergeEnemiesInfo(context)
    self._MergeBonusesInfo(context)
    self._MergeVisibleCells(context)

  def _MergeVisibleCells(self, context):
    global VISIBLE_CELLS
    if IsContinuingMove(context):
      context.MergeVisibleCells(VISIBLE_CELLS)
    VISIBLE_CELLS = context.visible_cells

  def _MergeBonusesInfo(self, context):
    global BONUSES
    if IsContinuingMove(context):
      res = {p: b for p, b in BONUSES.iteritems() if p != context.me.xy}
    else:
      res = {}

    for xy, bonus in context.bonuses.iteritems():
      res[xy] = bonus
    context.bonuses = res
    BONUSES = res

  def _MergeEnemiesInfo(self, context):
    # TODO: Don't totally drop enemies between turns.
    global ENEMIES
    global PREV_ACTION
    if IsContinuingMove(context):
      res = ENEMIES
    elif context.me.type != PREV_MOVE_TYPE:
      def CanSeeHim(enemy):
        # If I can see him, he'll be in the context.enemies list.
        return any(util.CanSee(context, ally, enemy) for ally in context.allies.itervalues())

      def ReliableInfo(enemy):
        # len(UNITS_ORDER) < TOTAL_UNITS means this is very first move.
        if len(global_vars.UNITS_ORDER) < global_vars.UNITS_IN_GAME:
          return True
        if enemy.type == context.me.type:
          return global_vars.GetPlayerOrder(enemy) == PlayerOrder.AFTER_ME
        if enemy.type == PREV_MOVE_TYPE:
          return global_vars.GetPlayerOrder(enemy) == PlayerOrder.BEFORE_ME
        return not UnitsMoveInOrder(PREV_MOVE_TYPE, enemy.type, context.me.type)

      res = dict([(p, enemy) for p, enemy in ENEMIES.iteritems() if ReliableInfo(enemy) and not CanSeeHim(enemy)])
    else:
      # Only one unit left. Everyone had a chance to move.
      res = {}

    for xy, enemy in context.enemies.iteritems():
      res[xy] = enemy
    context.enemies = res
    ENEMIES = res
    global_vars.UpdateSeenEnemies(context, context.enemies.keys())

  def AdjustEnemiesToDmg(self, xy, dmg):
    global ENEMIES, KILLED
    if xy in ENEMIES:
      if dmg > ENEMIES[xy].hitpoints:
        global_vars.ALIVE_ENEMIES[ENEMIES[xy].type] = False
        KILLED.add(UID(ENEMIES[xy]))
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
        self.AdjustEnemiesToDmg(PointAndDir(xy, d), context.game.grenade_collateral_damage)

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
        for S in params.ALL_STANCES:
          can_see = False
          for p in context.allies.itervalues():
            discount = 0 if p.type == TrooperType.SCOUT else context.game.sniper_prone_stealth_bonus
            sniper_vision_range = p.vision_range - discount
            can_see |= util.IsVisible(context, sniper_vision_range, p.x, p.y, p.stance, where.x, where.y, S)
          if not can_see and util.IsVisible(context, my_shooting_range, me.x, me.y, me.stance, where.x, where.y, S):
            return True
        return False

      bd = 1000
      found = False
      for x in range(int(me.x - my_shooting_range), int(me.x + my_shooting_range + 1.01)):
        for y in range(int(me.y - my_shooting_range), int(me.y + my_shooting_range + 1.01)):
          where = Point(x, y)
          if context.IsPassable(where):
            value = util.ManhDist(where, global_vars.NextGoal()) #global_vars.cell_vision[TrooperStance.PRONE][x][y] - len(global_vars.cell_dominated_by[TrooperStance.PRONE][x][y])
            if value < bd and ShootInvisible(where):
              move.action = ActionType.SHOOT
              move.x, move.y = x, y
              bd = value
              found = True

      if found:
        return
    if me.action_points >= 2 * util.MoveCost(context, me.stance):
      g = global_vars.NextGoal()
      for d in ALL_DIRS:
        p1 = PointAndDir(me.xy, d)
        if context.CanMoveTo(p1) and util.ManhDist(p1, g) < util.ManhDist(me.xy, g):
          move.action = ActionType.MOVE
          move.x, move.y = p1.x, p1.y
          global_vars.FORCED_ACTIONS = [actions.Walk(context, me.xy)]
          global_vars.FORCED_MOVE_ID = context.world.move_index, me.type
          global_vars.FORCED_MOVE_WITH_ENEMIES = bool(context.enemies)
          return
    # Try this:
    if me.action_points >= 2 and me.stance == TrooperStance.STANDING:
      move.action = ActionType.LOWER_STANCE
      return

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
    global PREV_MOVE_TYPE, PREV_MOVE_INDEX, PREV_ACTION, PREV_XY
    PREV_MOVE_TYPE = me.type
    PREV_MOVE_INDEX = world.move_index
    PREV_ACTION = move.action
    PREV_XY = me.xy
    global_vars.TURN_INDEX += 1

  def CombatMove(self, context, move):
    print 'Battle! Enemies:', ', '.join(
        '%s: %s %s' % (xy, util.GetName(TrooperType, enemy.type), util.GetName(TrooperStance, enemy.stance))
        for xy, enemy in context.enemies.iteritems())
    searcher = BattleSearcher()
    return searcher.DoSearch(battle_evaluator.EvaluatePosition, context, move)

  def RealMove(self, context, move):
    if global_vars.FIRST_MOVES_RANDOM > context.world.move_index:
      return None

    if (global_vars.FORCED_ACTIONS and
        (context.world.move_index, context.me.type) == global_vars.FORCED_MOVE_ID and
        global_vars.FORCED_MOVE_WITH_ENEMIES == bool(context.enemies)):
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
      print 'Last seen:', global_vars.LAST_ENEMY_POSITION
      return scouting.ScoutingMove(context, move)

  def FillCornersOrder(self, context):
    """Finds another corner to run to at the start of the game (second closest corner to this trooper)."""
    me = context.me
    global_vars.ORDER_OF_CORNERS = []
    x = 0 if me.x < X / 2 else X - 1
    y = 0 if me.y < Y / 2 else Y - 1
    global_vars.ORDER_OF_CORNERS.append(util.ClosestEmptyCell(context, Point(x, y)))
    y = 0 if y > Y / 2 else Y - 1  # Switch y
    global_vars.ORDER_OF_CORNERS.append(util.ClosestEmptyCell(context, Point(x, y)))
    x = 0 if me.x > X / 2 else X - 1
    global_vars.ORDER_OF_CORNERS.append(util.ClosestEmptyCell(context, Point(x, y)))
    y = 0 if y > Y / 2 else Y - 1  # Switch y
    global_vars.ORDER_OF_CORNERS.append(util.ClosestEmptyCell(context, Point(x, y)))
    global_vars.NEXT_CORNER = 2 if context.IsDuel() else global_vars.ITERATION_ORDER

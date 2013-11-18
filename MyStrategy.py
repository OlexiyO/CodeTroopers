import cPickle as pickle
import os
from random import getrandbits
import time
from actions import Position, Medikit, Heal

from context import Context
import global_vars
from model.CellType import CellType
from model.ActionType import ActionType
from constants import *
from model.TrooperType import TrooperType
import params
from search import Searcher
import util

GOALS = []
INITIALIZED = False
TOTAL_UNITS = None
UNITS_ORDER = []
ENEMIES = {}
PREV_MOVE_INDEX = None
PREV_MOVE_TYPE = None
PREV_ACTION = None

LOG_DIR = None
STDOUT_LOGGING = True

Goal = namedtuple('Goal', ['loc', 'type'])

class GoalType:
  ENEMY = 0
  BONUS = 1
  SCOUT = 2
  GET_TOGETHER = 2


def UnitsMoveInOrder(u1, u2, u3):
  assert u1 != u2, '%s != %s' % (u1, u2)
  assert u2 != u3, '%s != %s' % (u2, u3)
  assert u1 != u3, '%s != %s' % (u1, u3)
  assert len(UNITS_ORDER) == TOTAL_UNITS
  n1 = UNITS_ORDER.index(u1)
  n2 = UNITS_ORDER.index(u2)
  n3 = UNITS_ORDER.index(u3)
  if n1 < n3:
    return n1 < n2 < n3
  else:
    return n2 > n1 or n2 < n3


class MyStrategy(object):

  def _PrecomputeDistances(self, context):
    row = [1000] * Y
    for x_ in xrange(X):
      for y_ in xrange(Y):
        if context.world.cells[x_][y_] == CellType.FREE:
          if x_ >= X / 2:
            other = global_vars.distances[X - x_ - 1][y_]
            global_vars.distances[x_][y_] = [other[X - i - 1] for i in xrange(X)]
            continue
          elif y_ >= Y / 2:
            other = global_vars.distances[x_][Y - y_ - 1]
            global_vars.distances[x_][y_] = [list(reversed(other[i])) for i in xrange(X)]
            continue
          data = [list(row) for _ in xrange(X)]
          data[x_][y_] = 0
          q = [None] * (X * Y)
          q[0] = Point(x_, y_)
          pos = 0
          lastp = 1
          while pos < lastp:
            p = q[pos]
            pos += 1
            t = data[p.x][p.y] + 1
            for d in ALL_DIRS:
              p1 = PointAndDir(p, d)
              if context.IsPassable(p1) and data[p1.x][p1.y] > t:
                data[p1.x][p1.y] = t
                q[lastp] = p1
                lastp += 1
          global_vars.distances[x_][y_] = data

  def Init(self, context):
    global INITIALIZED
    INITIALIZED = True
    global GOALS
    GOALS.append(Goal(FindCornerToRun(context.me), GoalType.SCOUT))
    global TOTAL_UNITS
    TOTAL_UNITS = len([t for t in context.world.troopers if t.teammate])
    if STDOUT_LOGGING:
      print 'Start from', context.me.x, context.me.y

    t = time.time()
    self._PrecomputeDistances(context)
    dt = time.time() - t
    if STDOUT_LOGGING:
      print '%.2f' % dt
    
  def _PreMove(self, context):
    global TOTAL_UNITS
    global UNITS_ORDER
    global ENEMIES
    global PREV_MOVE_INDEX
    global PREV_MOVE_TYPE
    if context.me.type not in UNITS_ORDER:
      assert context.world.move_index == 0, context.world.move_index
      UNITS_ORDER.append(context.me.type)
    
    # Update enemies.
    same_move = (context.world.move_index == PREV_MOVE_INDEX and
                 context.me.type == PREV_MOVE_TYPE)

    # TODO: Don't drop enemies between turns.
    res = None
    if same_move:
      if PREV_ACTION in [ActionType.SHOOT, ActionType.THROW_GRENADE]:
        # We were shooting -- so we could killed someone, and our vision didn't change.
        # It could changed if we killed ourselves, but we ignore this for now.
        res = {}
      else:
        # We were moving -- so enemies are still there.
        res = ENEMIES
    elif context.me.type != PREV_MOVE_TYPE:
      res = dict([(p, enemy) for p, enemy in ENEMIES.iteritems()
                  if (enemy.type != context.me.type and
                      enemy.type != PREV_MOVE_TYPE and
                      # len(UNITS_ORDER) < TOTAL_UNITS means this is very first move.
                      (len(UNITS_ORDER) < TOTAL_UNITS or not UnitsMoveInOrder(PREV_MOVE_TYPE, enemy.type, context.me.type)))])
    else:
      res = {}

    for xy, enemy in context.enemies.iteritems():
      res[xy] = enemy

    context.enemies = res
    ENEMIES = res
    return same_move

  def MaybeSaveLog(self, context):
    if LOG_DIR is None:
      return
    cv = context.world.cell_visibilities
    if global_vars.TURN_INDEX == 0:
      cv_file = os.path.join(LOG_DIR, 'visibilities')
      with open(cv_file, 'w') as cv_file:
        pickle.dump(cv, cv_file)
    context.world.cell_visibilities = None
    log_file = os.path.join(LOG_DIR, '%03d_%s_%s.pickle' % (global_vars.TURN_INDEX, context.world.move_index, context.me.type))
    with open(log_file, 'w') as fout:
      pickle.dump(context, fout)
    context.world.cell_visibilities = cv

  def move(self, me, world, game, move):
    print GOALS
    context = Context(me, world, game)
    self.MaybeSaveLog(context)
    global INITIALIZED
    if not INITIALIZED:
      self.Init(context)
    same_move = self._PreMove(context)
    self.RealMove(context, move)
    if move.action == ActionType.END_TURN and not same_move:
      for d in ALL_DIRS:
        p1 = PointAndDir(context.me_pos, d)
        if context.CanMoveTo(p1.x, p1.y):
          move.action = ActionType.MOVE
          move.x, move.y = p1.x, p1.y
          break

    if STDOUT_LOGGING:
      if move.action == ActionType.END_TURN:
        print 'Move %d, type %d at %02d:%02d' % (world.move_index, me.type, me.x, me.y), 'pass:', me.action_points
      else:
        print 'Move %d, type %d at %02d:%02d' % (world.move_index, me.type, me.x, me.y), 'Does:', move.action, move.x, move.y
    global PREV_MOVE_TYPE
    global PREV_MOVE_INDEX
    global PREV_ACTION
    PREV_MOVE_TYPE = me.type
    PREV_MOVE_INDEX = world.move_index
    PREV_ACTION = move.action
    global_vars.TURN_INDEX += 1

  def CombatMove(self, context, move):
    global GOALS
    (ex, ey), enemy = min(context.enemies.iteritems(), key=lambda x: x[1].hitpoints)
    GOALS = [g for g in GOALS if g.type != GoalType.ENEMY]
    GOALS.append(Goal(Point(x=ex, y=ey), GoalType.ENEMY))
    searcher = Searcher()
    action = searcher.DoSearch(context)
    action.SetMove(move)

  def RealMove(self, context, move):
    me = context.me

    while GOALS:
      if GOALS[-1].type == GoalType.SCOUT:
        md = max(util.Dist(p, GOALS[-1].loc) for p in context.allies)
        if md < 4:
          del GOALS[-1]
        else:
          break
      elif any(p == GOALS[-1].loc for p in context.allies):
        del GOALS[-1]
      else:
        break

    if me.action_points < 2:
      move.action = ActionType.END_TURN
      return

    if context.enemies:
      self.CombatMove(context, move)
    else:
      self.ScoutingMove(context, move)

  def ScoutingMove(self, context, move):
    me = context.me
    global GOALS
    position = Position(context)
    if (me.type == TrooperType.FIELD_MEDIC and
        me.action_points >= context.game.field_medic_heal_cost and
        self.MaybeHeal(position, context, move)):
      return

    if not any(ally.type == TrooperType.FIELD_MEDIC for ally in context.allies.values()):
      if (context.me.action_points >= context.game.medikit_use_cost and
          context.me.holding_medikit and
          self.MaybeMedikit(position, context, move)):
        return

    closest = None
    best_d = 1000
    for xy, bonus in context.bonuses.iteritems():
      if not position.HasBonus(bonus.type):
        d = util.Dist(xy, position.loc)
        if d < best_d:
          best_d, closest = d, xy
    if closest is not None:
      if not GOALS or GOALS[-1].type != GoalType.BONUS:
        GOALS.append(Goal(closest, GoalType.BONUS))
      if self.GoTo(closest, context, move, keep_together=True):
        return
    # TODO: Walk towards Bonuses even around other guys.
    if not GOALS:
      x_stays = getrandbits(1)
      x = 0 if ((me.x < X/2) ^ (not x_stays)) else X - 1
      y = 0 if ((me.y < Y/2) ^ x_stays) else Y - 1
      g = Point(x, y)
      if STDOUT_LOGGING:
        print 'New scouting goal:', x_stays, me.x, me.y, g
      if g in context.allies or context.world.cells != CellType.FREE:
        g = ClosestEmptyCell(context, g)
      GOALS.append(Goal(g, GoalType.SCOUT))
    gtype, where = GOALS[-1].type, GOALS[-1].loc
    if gtype == GoalType.BONUS:
      bonus = context.bonuses.get(where, None)
      if bonus is not None and position.HasBonus(bonus.type) and context.steps[where.x][where.y] < 3:
        return
    if GOALS[-1].loc == context.me_pos or not self.GoTo(GOALS[-1].loc, context, move):
      move.action = ActionType.END_TURN

  def RunAway(self, where, context, move):
    data = global_vars.distances[where.x][where.y]
    me = context.me
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if context.CanMoveTo(x1, y1) and data[x1][y1] > current_dist:
        move.action = ActionType.MOVE
        move.x, move.y = x1, y1
        return True
    return False

  @util.TimeMe
  def GoTo(self, where, context, move, keep_together=False):
    """Tells unit 'me' to run to 'where'."""
    assert where != context.me_pos
    p = where
    last = context.steps[p.x][p.y]
    xy = None
    if last < 100:
      while True:
        if last == 1:
          xy = p
          break
        found = False
        for d in ALL_DIRS:
          p1 = PointAndDir(p, d)
          if context.CanMoveTo(p1.x, p1.y) and context.steps[p1.x][p1.y] == last - 1:
            found = True
            last -= 1
            p = p1
            break
        if not found:
          return False
    else:
      dmap = global_vars.distances[where.x][where.y]
      now = dmap[context.me.x][context.me.y]
      for d in ALL_DIRS:
        p1 = PointAndDir(context.me_pos, d)
        if context.CanMoveTo(p1.x, p1.y) and dmap[p1.x][p1.y] == now - 1:
          xy = p1
          break

    if xy is None:
      return False
    #if keep_together:
    tfa = DistFromHerd(context, xy)
    if tfa > params.TOO_FAR_APART and tfa > DistFromHerd(context, context.me_pos):
      return False
    move.action = ActionType.MOVE
    move.x, move.y = xy.x, xy.y
    return True

  def _FindMostMissingHP(self, position, context):
    most_missing, where = 0, None
    for xy, ally in context.allies.iteritems():
      will_heal = min(
          ally.maximal_hitpoints - ally.hitpoints,
          context.game.medikit_heal_self_bonus_hitpoints if xy == position.loc else context.game.medikit_bonus_hitpoints)
      if will_heal > most_missing:
        most_missing, where = will_heal, xy
    return most_missing, where

  def MaybeMedikit(self, position, context, move):
    most_missing, where = self._FindMostMissingHP(position, context)
    if most_missing > 0:
      if util.NextCell(where, position.loc) or where == position.loc:
        act = Medikit(context, where)
        assert act.Allowed(position)
        act.SetMove(move)
        return True
      else:
        self.GoTo(where, context, move)
        return True
    return False

  def MaybeHeal(self, position, context, move):
    most_missing, where = self._FindMostMissingHP(position, context)
    if most_missing > 0:
      if util.NextCell(where, position.loc) or where == position.loc:
        act = Heal(context, where)
        assert act.Allowed(position)
        act.SetMove(move)
        return True
      else:
        self.GoTo(where, context, move)
        return True
    return False


def FindCornerToRun(trooper):
  """Finds another corner to run to at the start of the game (second closest corner to this trooper)."""
  assert trooper.teammate
  x = 0 if trooper.x < X / 2 else X - 1
  y = 0 if (trooper.y > (Y / 2)) else Y - 1
  return Point(x=x, y=y)


def ClosestEmptyCell(context, to):
  for dist in range(1, 10):
    for dx in range(dist + 1):
      for dy in range(dist + 1 - dx):
        for x in (-dx, dx):
          for y in (-dy, dy):
            if context.CanMoveTo(to.x + x, to.y + y):
              return Point(to.x + x, to.y + y)
  return None


def DistFromHerd(context, p):
  D = global_vars.distances[p.x][p.y]
  return max(D[xy.x][xy.y] for xy in context.allies)

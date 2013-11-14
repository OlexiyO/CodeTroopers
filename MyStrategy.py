from random import getrandbits
import time

from context import Context
from model.CellType import CellType
from model.ActionType import ActionType
from model.Direction import Direction
from model.Game import Game
from model.Move import Move
from model.Trooper import Trooper
from model.TrooperStance import TrooperStance
from model.World import World
from constants import *
import plan
import util

# TODO: Move everything to globals.
GOAL = None
INITIALIZED = False
TOTAL_UNITS = None
UNITS_ORDER = []
ENEMIES = {}
distances = [list([None] * Y) for _ in xrange(X)]
PREV_MOVE_INDEX = None
PREV_MOVE_TYPE = None
PREV_ACTION = None


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
            other = distances[X - x_ - 1][y_]
            distances[x_][y_] = [other[X - i - 1] for i in xrange(X)]
            continue
          elif y_ >= Y / 2:
            other = distances[x_][Y - y_ - 1]
            distances[x_][y_] = [list(reversed(other[i])) for i in xrange(X)]
            continue
          data = [list(row) for _ in xrange(X)]
          data[x_][y_] = 0
          q = [0] * (2 * X * Y)
          q[0] = x_
          q[1] = y_
          pos = 0
          lastp = 2
          while pos < lastp:
            x, y = q[pos], q[pos + 1]
            pos += 2
            t = data[x][y] + 1
            for d in ALL_DIRS:
              x1 = x + d.x
              y1 = y + d.y
              if context.IsPassable(x1, y1) and data[x1][y1] > t:
                data[x1][y1] = t
                q[lastp] = x1
                q[lastp + 1] = y1
                lastp += 2
          distances[x_][y_] = data

  def Init(self, context):
    global INITIALIZED
    INITIALIZED = True
    global GOAL
    GOAL = FindCornerToRun(context.me)
    global TOTAL_UNITS
    TOTAL_UNITS = len([t for t in context.world.troopers if t.teammate])

    t = time.time()
    self._PrecomputeDistances(context)
    dt = time.time() - t
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
    else:
      res = dict([(p, enemy) for p, enemy in ENEMIES.iteritems()
                  if (enemy.type != context.me.type and
                      enemy.type != PREV_MOVE_TYPE and
                      not UnitsMoveInOrder(PREV_MOVE_TYPE, enemy.type, context.me.type))])

    for xy, enemy in context.enemies.iteritems():
      res[xy] = enemy

    context.enemies = res
    ENEMIES = res

  # TODO: Refactor move into Before --> Decide --> After

  def move(self, me, world, game, move):
    self.RealMove(me, world, game, move)
    if move.action == ActionType.END_TURN:
      print 'pass'
    else:
      print 'Type %d at %02d:%02d' % (me.type, me.x, me.y), 'Does:', move.action, move.x, move.y
    global PREV_MOVE_TYPE
    global PREV_MOVE_INDEX
    global PREV_ACTION
    PREV_MOVE_TYPE = me.type
    PREV_MOVE_INDEX = world.move_index
    PREV_ACTION = move.action

  def RealMove(self, me, world, game, move):
    context = Context(me, world, game)
    global INITIALIZED
    if not INITIALIZED:
      self.Init(context)
    self._PreMove(context)
    
    if me.action_points < 2:
      move.action = ActionType.END_TURN
      return

    global GOAL
    if context.enemies:
      (ex, ey), enemy = min(context.enemies.iteritems(), key=lambda x: x[1].hitpoints)
      GOAL = Point(x=ex, y=ey)
    elif GOAL is None:
      x_stays = getrandbits(1)
      x = 0 if ((me.x < X/2) ^ (not x_stays)) else X - 1
      y = 0 if ((me.y < Y/2) ^ x_stays) else Y - 1
      print 'GGGG', x_stays, me.x, me.y, x, y
      GOAL = Point(x=x, y=y)
      if GOAL in context.allies or context.world.cells != CellType.FREE:
        GOAL = ClosestEmptyCell(context, GOAL)

    tactics = []
    # TODO: Write simple DFS for actions on each step.

    if context.enemies and me.holding_field_ration:
      move.action = ActionType.EAT_FIELD_RATION
      return

    for where, enemy in context.enemies.iteritems():
      tactics.append(plan.ShootDirect(context, where))
      for d in ALL_DIRS:
        p1 = Point(x=where.x + d.x, y=where.y + d.y)
        tactics.append(plan.ThrowGrenade(context, p1))
    tactics.append(plan.HealYourself(context))

    tactics = [t for t in tactics if t.IsPossible()]
    if tactics:
      best = tactics[0]
      for t in tactics[1:]:
        if t.IsBetter(best):
          best = t
      if best.GetProfit() > 0:
        best.SetNextStep(move)
        return

    if context.enemies:
      if me.action_points >= me.shoot_cost + util.MoveCost(me, game):
        if self.GoTo(GOAL, context, move):
          if move.x == GOAL.x and move.y == GOAL.y:
            print 'achieved'
            GOAL = None
          return
        move.action = ActionType.END_TURN
      elif self.RunAway(GOAL, context, move):
        return
      move.action = ActionType.END_TURN
      return
    else:
      if self.GoTo(GOAL, context, move):
        pass
      else:
        move.action = ActionType.END_TURN
      dist = distances[GOAL.x][GOAL.y]
      md = max(dist[p.x][p.y] for p in context.allies)
      if md < 4:
        GOAL = None

  def RunAway(self, where, context, move):
    data = distances[where.x][where.y]
    me = context.me
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if context.CanMoveTo(x1, y1) and data[x1][y1] > current_dist:
        move.action = ActionType.MOVE
        move.x, move.y = x1, y1
        return True
    return False

  def GoTo(self, where, context, move):
    """Tells unit 'me' to run to 'where'."""
    data = distances[where.x][where.y]
    me = context.me
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if context.CanMoveTo(x1, y1) and data[x1][y1] < current_dist:
        move.action = ActionType.MOVE
        move.x, move.y = x1, y1
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

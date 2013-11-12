from random import getrandbits
import time

from collections import namedtuple
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


GOAL = None
INITIALIZED = False
distances = [list([None] * Y) for _ in xrange(X)]

def logmove(func):
  def F(*args, **kwargs):
    func(*args, **kwargs)
    move = args[-1]
    if move.action == ActionType.END_TURN:
      print 'pass'
    else:
      print move.action, move.x, move.y
  return F


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
              if context.IsPassable(x1, y1) and (data[x1][y1] > t):
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

    t = time.time()
    self._PrecomputeDistances(context)
    dt = time.time() - t
    print '%.2f' % dt

  @logmove
  def move(self, me, world, game, move):
    context = Context(me, world, game)
    global INITIALIZED
    if not INITIALIZED:
      self.Init(context)
    global UNITS
    UNITS = {(T.x, T.y) : T for T in world.troopers}
    if me.action_points < 2:
      move.action = ActionType.END_TURN
      return

    enemies = {xy: T for xy, T in UNITS.iteritems() if not T.teammate}
    global GOAL
    if enemies:
      (ex, ey), enemy = min(enemies.iteritems(), key=lambda x: x[1].hitpoints)
      GOAL = Point(x=ex, y=ey)
    elif GOAL is None:
      x_stays = getrandbits(1)
      x = 0 if ((me.x < X/2) ^ (not x_stays)) else X - 1
      y = 0 if ((me.y < Y/2) ^ x_stays) else Y - 1
      print 'GGGG', x_stays, me.x, me.y, x, y
      GOAL = Point(x=x, y=y)

    if enemies:
      (ex, ey), enemy = min(enemies.iteritems(), key=lambda x: x[1].hitpoints)
      if (me.holding_grenade and
          me.action_points >= game.grenade_throw_cost and
          me.get_distance_to(ex, ey) <= game.grenade_throw_range and
          enemy.hitpoints >= game.grenade_direct_damage / 2):
        move.action = ActionType.THROW_GRENADE
        move.x = ex
        move.y = ey
        return
      elif me.action_points >= me.shoot_cost and CanShoot(me, enemy, world):
        move.action = ActionType.SHOOT
        move.x, move.y = ex, ey
        return
      elif me.action_points >= me.shoot_cost + MoveCost(me, game):
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
        if move.x == GOAL.x and move.y == GOAL.y:
          print 'achieved'
          GOAL = None
        return
      else:
        move.action = ActionType.END_TURN

  def RunAway(self, where, context, move):
    data = distances[where.x][where.y]
    me = context.me
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if context.IsPassable(x1, y1) and data[x1][y1] > current_dist:
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
      if context.IsPassable(x1, y1) and data[x1][y1] < current_dist:
        move.action = ActionType.MOVE
        move.x, move.y = x1, y1
        return True
    return False


def CanShoot(me, enemy, world):
  return world.is_visible(me.shooting_range, me.x, me.y, me.stance, enemy.x, enemy.y, enemy.stance)


def FindCornerToRun(trooper):
  """Finds another corner to run to at the start of the game (second closest corner to this trooper)."""
  assert trooper.teammate
  x = 0 if trooper.x < X / 2 else X - 1
  y = 0 if (trooper.y > (Y / 2)) else Y - 1
  return Point(x=x, y=y)


def MoveCost(trooper, game):
  if trooper.stance == TrooperStance.STANDING:
    return game.standing_move_cost
  elif trooper.stance == TrooperStance.KNEELING:
    return game.kneeling_move_cost
  else:
    assert trooper.stance == TrooperStance.PRONE
    return game.prone_move_cost
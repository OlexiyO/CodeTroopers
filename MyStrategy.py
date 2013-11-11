from collections import namedtuple
from model.CellType import CellType
from model.ActionType import ActionType
from model.Direction import Direction
from model.Game import Game
from model.Move import Move
from model.Trooper import Trooper
from model.TrooperStance import TrooperStance
from model.World import World


Point = namedtuple('Point', ['x', 'y'])
NORTH = Point(x=0, y=-1)
SOUTH = Point(x=0, y=1)
EAST = Point(x=1, y=0)
WEST = Point(x=-1, y=0)
ALL_DIRS = [NORTH, SOUTH, EAST, WEST]
Y = 20
X = 30
CELLS = None
GOAL = None
INITIALIZED = False
distances = [list([None] * Y) for _ in xrange(X)]
UNITS = {}

IsInside = lambda x, y: (0 <= x < X) and (0 <= y < Y)
IsPassable = lambda x, y: IsInside(x, y) and CELLS[x][y] == 0 and (x, y) not in UNITS

def logmove(func):
  def F(*args, **kwargs):
    func(*args, **kwargs)
    move = args[-1]
    print move.action, move.x, move.y
  return F


class MyStrategy(object):

  def _PrecomputeDistances(self):
    row = [1000] * Y
    for x_ in xrange(X):
      for y_ in xrange(Y):
        if CELLS[x_][y_] == CellType.FREE:
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
              if IsPassable(x1, y1) and (data[x1][y1] > t):
                data[x1][y1] = t
                q[lastp] = x1
                q[lastp + 1] = y1
                lastp += 2
          distances[x_][y_] = data

  def Init(self, me, world, game):
    global INITIALIZED
    INITIALIZED = True
    global CELLS
    if CELLS is None:
      CELLS = world.cells
    global GOAL
    GOAL = FindCornerToRun(me)

    import time
    t = time.time()
    self._PrecomputeDistances()
    dt = time.time() - t
    print dt

  @logmove
  def move(self, me, world, game, move):
    global INITIALIZED
    if not INITIALIZED:
      self.Init(me, world, game)
    global UNITS
    UNITS = {(T.x, T.y) : T for T in world.troopers}
    if me.action_points < 2:
      move.action = ActionType.END_TURN
      return

    enemies = {xy: T for xy, T in UNITS.iteritems() if not T.teammate}
    if enemies:
      (ex, ey), enemy = min(enemies.iteritems(), key=lambda x: x[1].hitpoints)
      global GOAL
      GOAL = Point(x=ex, y=ey)
      if me.action_points >= me.shoot_cost and CanShoot(me, enemy, world):
        move.action = ActionType.SHOOT
        move.x, move.y = ex, ey
        return
      elif self.RunAway(GOAL, me, world, game, move):
        return
      move.action = ActionType.END_TURN
      return
    elif self.GoTo(GOAL, me, world, game, move):
      return
    else:
      move.action = ActionType.END_TURN

  def RunAway(self, where, me, world, game, move):
    data = distances[where.x][where.y]
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if IsPassable(x1, y1) and data[x1][y1] > current_dist:
        move.action = ActionType.MOVE
        move.x, move.y = x1, y1
        return True
    return False

  def GoTo(self, where, me, world, game, move):
    data = distances[where.x][where.y]
    current_dist = data[me.x][me.y]
    for dir in ALL_DIRS:
      x1, y1 = me.x + dir.x, me.y + dir.y
      if IsPassable(x1, y1) and data[x1][y1] < current_dist:
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
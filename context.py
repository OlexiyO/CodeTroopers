from constants import *
from model.CellType import CellType
import util

row = [1000] * Y

class Context(object):
  def __init__(self, me, world, game):
    self.me = me
    self.me_pos = Point(me.x, me.y)
    self.world = world
    self.game = game
    self.units = {Point(T.x, T.y) : T for T in world.troopers}
    self.enemies = {p: T for p, T in self.units.iteritems() if not T.teammate}
    self.allies = {p: T for p, T in self.units.iteritems() if T.teammate}
    self.bonuses = {Point(b.x, b.y): b for b in self.world.bonuses}
    self._FillDistances()

  def IsInside(self, p):
    return (0 <= p.x < X) and (0 <= p.y < Y)

  def IsPassable(self, p):
    return self.IsInside(p) and self.world.cells[p.x][p.y] == CellType.FREE

  def CanMoveTo(self, x, y):
    p = Point(x, y)
    return self.IsPassable(p) and p not in self.units

  def GetEnemyAt(self, point):
    return self.enemies.get(point, None)

  def CanHaveHiddenEnemy(self, point):
    if not self.IsInside(point):
      return False
    if self.world.cells[point.x][point.y] != CellType.FREE:
      return False
    return True

  @util.TimeMe
  def _FillDistances(self):
    self.steps = [list(row) for _ in xrange(X)]
    q = [None] * (X * Y)
    q[0] = self.me_pos
    pos = 0
    lastp = 1
    self.steps[self.me.x][self.me.y] = 0
    while pos < lastp:
      p = q[pos]
      pos += 1
      t = self.steps[p.x][p.y] + 1
      if t > 9:
        break
      for d in ALL_DIRS:
        p1 = PointAndDir(p, d)
        if self.CanMoveTo(p1.x, p1.y) and self.steps[p1.x][p1.y] > t:
          self.steps[p1.x][p1.y] = t
          q[lastp] = p1
          lastp += 1

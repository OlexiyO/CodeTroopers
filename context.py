from constants import *
from model.CellType import CellType

class Context(object):
  def __init__(self, me, world, game):
    self.me = me
    self.world = world
    self.game = game
    self.units = {Point(T.x, T.y) : T for T in world.troopers}
    self.enemies = {p: T for p, T in self.units.iteritems() if not T.teammate}
    self.allies = {p: T for p, T in self.units.iteritems() if T.teammate}
    self.bonuses = {Point(b.x, b.y): b for b in self.world.bonuses}

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

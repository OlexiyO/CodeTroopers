from constants import *
from model.CellType import CellType

class Context(object):
  def __init__(self, me, world, game):
    self.me = me
    self.world = world
    self.game = game
    self.units = {Point(x=T.x, y=T.y) : T for T in world.troopers}
    self.enemies = {p: T for p, T in self.units.iteritems() if not T.teammate}
    self.allies = {p: T for p, T in self.units.iteritems() if T.teammate}
    self.bonuses = {Point(x=b.x, y=b.x): b for b in self.world.bonuses}

  def IsInside(self, x, y):
    return (0 <= x < X) and (0 <= y < Y)

  def IsPassable(self, x, y):
    return self.IsInside(x, y) and self.world.cells[x][y] == CellType.FREE

  def CanMoveTo(self, x, y):
    return self.IsPassable(x, y) and Point(x=x, y=y) not in self.units

  def GetEnemyAt(self, point):
    return self.enemies.get(point, None)

  def CanHaveHiddenEnemy(self, point):
    if not self.IsInside(point.x, point.y):
      return False
    if self.world.cells[point.x][point.y] != CellType.FREE:
      return False
    return True

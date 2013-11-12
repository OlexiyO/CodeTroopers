from constants import *

class Context(object):
  def __init__(self, me, world, game):
    self.me = me
    self.world = world
    self.game = game
    self.units = {(T.x, T.y) : T for T in world.troopers}
    self.enemies = {xy: T for xy, T in self.units.iteritems() if not T.teammate}

  def IsInside(self, x, y):
    return (0 <= x < X) and (0 <= y < Y)

  def IsPassable(self, x, y):
    return self.IsInside(x, y) and self.world.cells[x][y] == 0 and (x, y) not in self.units


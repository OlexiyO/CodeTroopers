from constants import *
import global_vars
import map_util
from model.CellType import CellType
import params
import util

row = [1000] * Y


class Context(object):
  def __init__(self, me, world, game):
    self.me = me
    self.me.xy = Point(me.x, me.y)
    self.world = world
    self.map_name = map_util.MapName(self)
    self.game = game
    self.units = {Point(T.x, T.y) : T for T in world.troopers}
    for u in self.units.itervalues():
      u.xy = Point(u.x, u.y)
    self.enemies = {p: T for p, T in self.units.iteritems() if not T.teammate}
    self.allies = {p: T for p, T in self.units.iteritems() if T.teammate}
    self.bonuses = {Point(b.x, b.y): b for b in self.world.bonuses}

    # For tests.
    self.TOTAL_UNITS = global_vars.UNITS_IN_GAME
    self.UNITS_ORDER = global_vars.UNITS_ORDER
    self.NEXT_CORNER = global_vars.NEXT_CORNER
    self.ORDER_OF_CORNERS = global_vars.ORDER_OF_CORNERS

  def IsInside(self, p):
    return (0 <= p.x < X) and (0 <= p.y < Y)

  def IsPassable(self, p):
    return self.IsInside(p) and self.world.cells[p.x][p.y] == CellType.FREE

  @util.TimeMe
  def CanMoveTo(self, p):
    return self.IsPassable(p) and p not in self.units

  def IsDuel(self):
    return len(self.world.players) == 2
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

    self.officer = self._GetCommandingOfficer()
    self._FillDistancesFromMe()
    self._FillVisibleCells()

    self.TOTAL_UNITS = global_vars.UNITS_IN_GAME
    self.UNITS_ORDER = global_vars.UNITS_ORDER
    self.NEXT_CORNER = global_vars.NEXT_CORNER
    self.ORDER_OF_CORNERS = global_vars.ORDER_OF_CORNERS

  def IsCommandingOfficer(self, trooper):
    return self.officer.type == trooper.type

  def _GetCommandingOfficer(self):
    for trooper_type in params.COMMANDING_ORDER:
      for who in self.allies.itervalues():
        if who.type == trooper_type:
          return who
    assert False

  def IsInside(self, p):
    return (0 <= p.x < X) and (0 <= p.y < Y)

  def IsPassable(self, p):
    return self.IsInside(p) and self.world.cells[p.x][p.y] == CellType.FREE

  @util.TimeMe
  def CanMoveTo(self, p):
    return self.IsPassable(p) and p not in self.units

  def GetEnemyAt(self, point):
    return self.enemies.get(point, None)

  def CanHaveHiddenEnemy(self, point):
    return self.IsInside(point) and self.world.cells[point.x][point.y] == CellType.FREE

  @util.TimeMe
  def _FillDistancesFromMe(self):
    self.steps = self.FindDistances(self.me.xy)

  def MapIsOpen(self):
    return map_util.MapIsOpen(self.map_name)

  @util.TimeMe
  def FindDistances(self, where, maxd=10):
    data = util.Array2D(1000)
    q = [None] * (X * Y)
    q[0] = where
    pos = 0
    lastp = 1
    data[where.x][where.y] = 0
    while pos < lastp:
      p = q[pos]
      pos += 1
      t = data[p.x][p.y] + 1
      if t > maxd:
        break
      for d in ALL_DIRS:
        p1 = PointAndDir(p, d)
        if self.IsPassable(p1) and data[p1.x][p1.y] > t:
          data[p1.x][p1.y] = t
          if self.CanMoveTo(p1):
            q[lastp] = p1
            lastp += 1
    return data

  def DistFromHerd(self, who, where):
    if len(self.allies) == 1:
      return 0
    if self.officer.type == who.type:
      return max(global_vars.distances[where.x][where.y][p.x][p.y]
        for p, unit in self.allies.iteritems() if unit.type != self.officer.type)
    else:
      return global_vars.distances[self.officer.x][self.officer.y][where.x][where.y]

  def CloseEnough(self):
    return params.CLOSE_ENOUGH_2_UNITS + len(self.allies) - 2

  def IsVisible(self, p, stance):
    return self.visible_cells[stance][p.x][p.y]

  @util.TimeMe
  def _FillVisibleCells(self):
    self.visible_cells = [util.Array2D(False), util.Array2D(False), util.Array2D(False)]
    for stance in params.ALL_STANCES:
      for x in range(X):
        for y in range(Y):
          self.visible_cells[stance][x][y] = any(
              util.IsVisible(self, ally.vision_range, ally.x, ally.y, stance, x, y, stance)
              for ally in self.allies.itervalues())

  def MergeVisibleCells(self, CELLS):
    if CELLS is None:
      return
    for stance in params.ALL_STANCES:
      for x in range(X):
        for y in range(Y):
          self.visible_cells[stance][x][y] |= CELLS[stance][x][y]
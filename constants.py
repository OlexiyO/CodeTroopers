LOG_DIR = None

from collections import namedtuple
Point = namedtuple('Point', ['x', 'y'])
NORTH = Point(x=0, y=-1)
SOUTH = Point(x=0, y=1)
EAST = Point(x=1, y=0)
WEST = Point(x=-1, y=0)
ALL_DIRS = [NORTH, EAST, SOUTH, WEST]
Y = 20
X = 30
TOTAL_UNIT_TYPES = 5

def PointAndDir(p, d):
  return Point(p.x + d.x, p.y + d.y)
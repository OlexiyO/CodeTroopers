"""The most popular constants for this contest."""
from collections import namedtuple
from model.BonusType import BonusType
from model.TrooperStance import TrooperStance


LOG_DIR = None
ALL_STANCES = sorted([TrooperStance.PRONE, TrooperStance.KNEELING, TrooperStance.STANDING])
ALL_BONUSES = sorted([BonusType.MEDIKIT, BonusType.FIELD_RATION, BonusType.GRENADE])
Point = namedtuple('Point', ['x', 'y'])
NORTH = Point(x=0, y=-1)
SOUTH = Point(x=0, y=1)
EAST = Point(x=1, y=0)
WEST = Point(x=-1, y=0)
ALL_DIRS = [NORTH, EAST, SOUTH, WEST]
Y = 20
X = 30
TOTAL_UNIT_TYPES = 5

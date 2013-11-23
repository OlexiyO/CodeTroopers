from constants import *
distances = [list([None] * Y) for _ in xrange(X)]

INITIALIZED = False
TURN_INDEX = 0
FIRST_MOVES_RANDOM = 0
TOTAL_UNITS = []
UNITS_ORDER = []
SAW_ENEMY_LAST_TURN = False
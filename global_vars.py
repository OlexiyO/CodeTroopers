distances = []
cell_vision = []
cell_dominated_by = []

AT_HOME = False
INITIALIZED = False
STDOUT_LOGGING = True
TURN_INDEX = 0
FIRST_MOVES_RANDOM = 0

UNITS_IN_GAME = None
UNITS_ORDER = []
ORDER_OF_CORNERS = None
NEXT_CORNER = 3

MOVE_INDEX = None
FORCED_ACTIONS = []


def NextCorner():
  return ORDER_OF_CORNERS[NEXT_CORNER]

SNIPER_SHOOTING_RANGE = 10
POSITION_AT_START_MOVE = None

def ManhDist(A, B):
  return distances[A.x][A.y][B.x][B.y]
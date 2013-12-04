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
ITERATION_ORDER = 1  # 3 == First along long wall
NEXT_CORNER = ITERATION_ORDER
NEXT_GOAL = None

FORCED_MOVE_ID = None
FORCED_ACTIONS = []
LAST_SEEN_ENEMIES = 0


def NextGoal():
  if NEXT_GOAL is not None:
    return NEXT_GOAL
  return ORDER_OF_CORNERS[NEXT_CORNER]

SNIPER_SHOOTING_RANGE = 10
POSITION_AT_START_MOVE = None


def ManhDist(A, B):
  return distances[A.x][A.y][B.x][B.y]


def UpdateSeenEnemies(context):
  global NEXT_GOAL, LAST_SEEN_ENEMIES
  if context.enemies:
    NEXT_GOAL = context.enemies.keys()[0]
    LAST_SEEN_ENEMIES = context.world.move_index
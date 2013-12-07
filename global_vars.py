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
FORCED_MOVE_WITH_ENEMIES = False
LAST_SEEN_ENEMIES = 0
LAST_SWITCHED_GOAL = 0
LAST_ENEMY_POSITION = []
ALIVE_ENEMIES = [True] * 5


def NextGoal():
  if NEXT_GOAL is not None:
    return NEXT_GOAL
  return ORDER_OF_CORNERS[NEXT_CORNER]

SNIPER_SHOOTING_RANGE = 10
POSITION_AT_START_MOVE = None


def UpdateSeenEnemies(context, coords):
  global NEXT_GOAL, LAST_SEEN_ENEMIES, LAST_SWITCHED_GOAL, LAST_ENEMY_POSITION
  if coords:
    SetNextGoal(context, coords[0])
    LAST_SEEN_ENEMIES = context.world.move_index
    LAST_ENEMY_POSITION = list(coords)


def SwitchToNextGoal(move_index):
  global NEXT_CORNER, NEXT_GOAL, ITERATION_ORDER, LAST_SWITCHED_GOAL, LAST_ENEMY_POSITION
  if NEXT_GOAL is not None:
    NEXT_GOAL = None
  else:
    NEXT_CORNER = (NEXT_CORNER + ITERATION_ORDER) % 4
  LAST_ENEMY_POSITION = []
  LAST_SWITCHED_GOAL = move_index
  print 'NEXT', NextGoal()


def SetNextGoal(context, next_goal):
  global NEXT_GOAL, LAST_SWITCHED_GOAL
  NEXT_GOAL = next_goal
  LAST_SWITCHED_GOAL = context.world.move_index
  print 'NEXT', NextGoal()
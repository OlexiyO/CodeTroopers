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
ITERATION_ORDER = 1  # 3 == Go along long wall first
NEXT_CORNER = ITERATION_ORDER
NEXT_GOAL = None

FORCED_MOVE_ID = None
FORCED_ACTIONS = []
FORCED_MOVE_WITH_ENEMIES = False
LAST_SEEN_ENEMIES = 0
LAST_SWITCHED_GOAL = 0
LAST_ENEMY_POSITION = []
ALIVE_ENEMIES = [True] * 5

class PlayerOrder(object):
  UNKNOWN = 0
  BEFORE_ME = 1
  AFTER_ME = 2


ORDER_OF_PLAYERS = None
CONFIDENCE_ORDER = None

SNIPER_SHOOTING_RANGE = 10
POSITION_AT_START_MOVE = None


def NextGoal():
  if NEXT_GOAL is not None:
    return NEXT_GOAL
  return ORDER_OF_CORNERS[NEXT_CORNER]


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


def SetPlayerOrder(player_id, order, confidence):
  assert order != PlayerOrder.UNKNOWN
  global ORDER_OF_PLAYERS, CONFIDENCE_ORDER
  if ORDER_OF_PLAYERS[player_id] == PlayerOrder.UNKNOWN:
    ORDER_OF_PLAYERS[player_id] = order
    CONFIDENCE_ORDER[player_id] = confidence
    print
    print
    print
    print 'ORDER:', player_id, order
  else:
    if ORDER_OF_PLAYERS[player_id] != order:
      if CONFIDENCE_ORDER[player_id] < confidence:
        print 'Overriding order:', player_id, order
        ORDER_OF_PLAYERS[player_id] = order
      else:
        print 'Conflicting order: old vs new:', player_id, ORDER_OF_PLAYERS[player_id], order
    else:
      CONFIDENCE_ORDER[player_id] = max(confidence, CONFIDENCE_ORDER[player_id])


def GetPlayerOrder(unit):
  global ORDER_OF_PLAYERS
  return ORDER_OF_PLAYERS[unit.player_id]
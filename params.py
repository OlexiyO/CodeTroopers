from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType

KILL_EXTRA_PROFIT = 50
HIDDEN_NEIGHBOR_RATIO = 0.01
HEAL_DISCOUNT = .5  # Healing one point to yourself is that much worse than doing 1 point of damage.

SELF_KILL_PENALTY = 50   # Healing discount is NOT applied.

LOW_LIFE_CUTOFF = 20     # Life below this limit means low
LOW_LIFE_BONUS = .2      # Give extra points for subtracting every point below this limit.
BELOW_COLLATERAL_GRENADE_BONUS = .1
BELOW_DIRECT_GRENADE_BONUS = .05
assert BELOW_DIRECT_GRENADE_BONUS <= BELOW_COLLATERAL_GRENADE_BONUS <= LOW_LIFE_BONUS

SVD_BONUS_MULT = 5.
SVD_DISTANCE_RATIO = .2

EXTRA_ACTION_POINT_BONUS = 8
GOOD_CELL_VALUE_BONUS = .05
BAD_CELL_VALUE_PENALTY = 1.

CLOSE_ENOUGH_2_UNITS = 2
TOO_FAR_PENALTY = 5.

COMMANDING_ORDER = [TrooperType.COMMANDER, TrooperType.SNIPER, TrooperType.FIELD_MEDIC, TrooperType.SOLDIER, TrooperType.SCOUT]
ATTACKING_ORDER = [TrooperType.SCOUT, TrooperType.SOLDIER, TrooperType.FIELD_MEDIC, TrooperType.COMMANDER, TrooperType.SNIPER]
WRONG_ATTACKING_ORDER_MULT = 1.

NO_DANGER_IF_N_MOVES_LEFT = 3
ALL_STANCES = sorted([TrooperStance.PRONE, TrooperStance.KNEELING, TrooperStance.STANDING])
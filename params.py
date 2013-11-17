KILL_EXTRA_PROFIT = 50
HIDDEN_NEIGHBOR_RATIO = 0.01
HEAL_DISCOUNT = .3  # Healing one point to yourself is that much worse than doing 1 point of damage.

SELF_KILL_PENALTY = 20   # Healing discount is NOT applied.

LOW_LIFE_CUTOFF = 20     # Life below this limit means low
LOW_LIFE_BONUS = .2      # Give extra points for subtracting every point below this limit.
BELOW_COLLATERAL_GRENADE_BONUS = .1
BELOW_DIRECT_GRENADE_BONUS = .05
assert BELOW_DIRECT_GRENADE_BONUS <= BELOW_COLLATERAL_GRENADE_BONUS <= LOW_LIFE_BONUS

SVD_BONUS_MULT = 4
SVD_DISTANCE_RATIO = .2

HAS_GRENADE_BONUS = 10
HAS_MEDIKIT_BONUS = 10
HAS_ENERGIZER_BONUS = 10
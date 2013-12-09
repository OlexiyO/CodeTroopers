"""Params for the algorithm."""

# Killing a unit worth doing that much extra damage.
KILL_EXTRA_PROFIT = 50
# Penalize if max distance between units is at least this.
TOO_FAR_FROM_ALLIES = 7
# When simulating Battle, allow everyone shoot that many times.
BATTLE_SIMULATOR_NUM_ROUNDS = 2
# If I score this turn, I get 1 point. If I predict the next unit to shoot and score 1 point, I discount the prediction (because things may change).
PREDICTION_DISCOUNT = .8
# If no (visible) enemy can see us, add this number to position score.
ENEMIES_DONT_SEE_US_BONUS = 50
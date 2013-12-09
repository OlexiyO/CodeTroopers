from battle_evaluator import _HoldItemsBonus, _HealEffect
import constants
import global_vars
from model.BonusType import BonusType
from model.TrooperType import TrooperType
import params
import util


def EvaluatePosition(context, position):
  return _BenefitScore(context, position) - _DangerScore(context, position)


def _DangerScore(context, position):
  # How dangerous is position?
  # Don't run too fast -- get only 3 steps to the goal per turn.
  too_far = max(3, util.ManhDist(position.me.xy, global_vars.POSITION_AT_START_MOVE))
  walk_too_far = 5000 * (too_far - 3)
  # Do not go away from allies.
  too_far_penalty = TooFarFromAlliesPenalty(context, position) * 10000
  # If we have a scout, scout must go first.
  dont_go_before_scout_penalty = DontGoBeforeScoutPenalty(context, position) * 1000
  return dont_go_before_scout_penalty + too_far_penalty + walk_too_far


def _BenefitScore(context, position):
  # What is good about position:
  # Did we heal any ally?
  hp_improvement = _HealEffect(context, position) * 1.2
  # Did we pick up a bonus?
  items_bonus = _HoldItemsBonus(context, position)
  # Did we get closer to goal?
  dist_score = 100 - util.ManhDist(global_vars.NextGoal(), position.me.xy)
  return hp_improvement + items_bonus + dist_score * .5


def DontGoBeforeScoutPenalty(context, position):
  if position.me.type == TrooperType.SCOUT or not context.IsDuel():
    return 0
  scout_xy = None
  for xy, ally in context.allies.iteritems():
    if ally.type == TrooperType.SCOUT:
      scout_xy = xy
  if scout_xy is None:
    return 0

  current_dist_to_goal = util.ManhDist(position.me.xy, global_vars.NextGoal())
  scout_distance = util.ManhDist(scout_xy, global_vars.NextGoal())
  return max(0, scout_distance + 1 - current_dist_to_goal)


def TooFarFromAlliesPenalty(context, position):
  # Penalize if we go too far from our allies.
  if not context.allies:
    return 0
  original_manh_dist = max(util.ManhDist(global_vars.POSITION_AT_START_MOVE, xy) for xy in context.allies)
  current_manh_dist = max(util.ManhDist(position.me.xy, xy) for xy in context.allies)
  original_penalty = max(0, original_manh_dist - params.TOO_FAR_FROM_ALLIES)
  current_penalty = max(0, current_manh_dist - params.TOO_FAR_FROM_ALLIES)
  # If unit starts too far from others (as on some maps), we want it to run closer to friends.
  # But: we want it to be able to pick up bonuses on the way.
  MAX_WIN_PER_TURN = 3
  level_zero = max(0, original_penalty - MAX_WIN_PER_TURN)
  if current_penalty <= level_zero:
    return 0
  return current_penalty - level_zero

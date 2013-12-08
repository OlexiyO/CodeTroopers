from battle_evaluator import _HoldItemsBonus, _HealEffect
import global_vars
import map_util
from model.BonusType import BonusType
from model.TrooperType import TrooperType
import params
import util


def EvaluatePosition(context, position):
  if EverythingIsSafe(context, position):
    too_far_penalty = 0
    walk_too_far = 0
    dont_go_before_scout_penalty = 0
    visible_for_enemy_score = 0
  else:
    too_far = max(3, util.ManhDist(position.me.xy, global_vars.POSITION_AT_START_MOVE))
    walk_too_far = -5000 * (too_far - 3)
    too_far_penalty = TooFarFromHerdPenalty(context, position) * -10000
    dont_go_before_scout_penalty = DontGoBeforeScoutPenalty(context, position) * -1000
    visible_for_enemy_score = 0 # util.HowCanEnemySeeUs(context, position, global_vars.LAST_ENEMY_POSITION) * params.THEY_DONT_SEE_US_BONUS

  benefit_score = _BenefitScore(context, position)
  return benefit_score + too_far_penalty + walk_too_far + dont_go_before_scout_penalty + visible_for_enemy_score


def DontGoBeforeScoutPenalty(context, position):
  if position.me.type == TrooperType.SCOUT or not context.IsDuel():
    return 0
  scout_xy = None
  for xy, ally in context.allies.iteritems():
    if ally.type == TrooperType.SCOUT:
      scout_xy = xy
  if scout_xy is None:
    return 0

  #original_dist_to_goal = util.ManhDist(global_vars.POSITION_AT_START_MOVE, global_vars.NextGoal())
  current_dist_to_goal = util.ManhDist(position.me.xy, global_vars.NextGoal())
  scout_distance = util.ManhDist(scout_xy, global_vars.NextGoal())
  return max(0, scout_distance + 1 - current_dist_to_goal)



def EverythingIsSafe(context, position):
  return False
  #return len(context.world.players) == 2 and context.world.move_index == 0


def TooFarFromHerdPenalty(context, position):
  if not context.allies:
    return 0

  #go_to_unit = min(context.allies.itervalues(), key=lambda unit: unit.type)
  original_manh_dist = max(util.ManhDist(global_vars.POSITION_AT_START_MOVE, xy) for xy in context.allies)
  #original_manh_dist = util.ManhDist(global_vars.POSITION_AT_START_MOVE, go_to_unit)
  current_manh_dist = max(util.ManhDist(position.me.xy, xy) for xy in context.allies)
  #current_manh_dist = util.ManhDist(position.me.xy, go_to_unit)
  original_penalty = max(0, original_manh_dist - params.TOO_FAR_FROM_HERD)
  current_penalty = max(0, current_manh_dist - params.TOO_FAR_FROM_HERD)
  MAX_WIN_PER_TURN = 3
  level_zero = max(0, original_penalty - MAX_WIN_PER_TURN)
  if current_penalty <= level_zero:
    return 0
  return current_penalty - level_zero


def NeedBonus(context, position, bt):
  if position.HasBonus(bt):
    return False
  if position.me.type == TrooperType.COMMANDER and bt == BonusType.FIELD_RATION:
    return all(util.HasBonus(ally, bt) for ally in position.allies_by_type if ally is not None)
  if position.me.type == TrooperType.SNIPER and bt == BonusType.GRENADE:
    return all(util.HasBonus(ally, bt) for ally in position.allies_by_type if ally is not None)
  return True


def _BonusesScore(context, position):
  missing = False
  for bonus in context.bonuses.itervalues():
    missing |= any(not util.HasBonus(ally, bonus.type) for ally in context.allies.itervalues())
  if not missing:
    return 0

  scores = util.ComputeItemBonuses(context, position.me)
  btypes = [BonusType.MEDIKIT, BonusType.FIELD_RATION, BonusType.GRENADE]
  mults = []
  for bt in btypes:
    best_d = 1000
    for xy, pres in position.bonuses_present.iteritems():
      if pres:
        b = context.bonuses[xy]
        if b.type == bt:
          best_d = min(best_d, global_vars.distances[xy.x][xy.y][position.me.xy.x][position.me.xy.y])
    m = max(0, 1. - best_d * .1)
    if not NeedBonus(context, position, bt):
      if best_d == 0:
        m = 1.
      else:
        m = 1. + m / 2.

    mults.append(m)
  return sum(score * mult for score, mult in zip(scores, mults))


def _BenefitScore(context, position):
  hp_improvement = _HealEffect(context, position) * 1.2
  items_bonus = _HoldItemsBonus(context, position)
  dist_score = 100 - util.ManhDist(global_vars.NextGoal(), position.me.xy)
  return hp_improvement + items_bonus + dist_score * .5


def _GetCellDangerScore(context, position):
  move_cost = util.MoveCost(context, position.me.stance)
  if position.action_points >= params.NO_DANGER_IF_N_MOVES_LEFT * move_cost:
    return 0
  xy = position.me.xy
  invisible_enemies = [p for p in global_vars.cell_dominated_by[position.me.stance][xy.x][xy.y]
                       if not context.IsVisible(p, position.me.stance)]
  return len(invisible_enemies)


def _AttackingOrderPenalty(context, position):
  discount = 1 if map_util.RelaxAttackingOrder(context) else 0

  goal = global_vars.NextGoal()
  safety_dist = global_vars.distances[goal.x][goal.y]
  #safety_dist = global_vars.distances[officer.x][officer.y]
  my_attacking_order = params.ATTACKING_ORDER.index(position.me.type)
  old_danger = -1000 #-safety_dist[position.me.xy.x][position.me.xy.y]
  new_danger = -safety_dist[position.me.xy.x][position.me.xy.y]
  #if old_danger >= new_danger:
  #  return 0
  penalty = 0
  for xy, ally in context.allies.iteritems():
    if ally.type == position.me.type:
      continue
    if context.steps[ally.x][ally.y] > 10:
      continue
    his_attacking_order = params.ATTACKING_ORDER.index(ally.type)
    if his_attacking_order > my_attacking_order:
      continue
    his_danger = -safety_dist[xy.x][xy.y]
    delta_danger = min((new_danger - his_danger - discount), 4)
    if delta_danger > 0:
      penalty += (delta_danger ** 2) * ((my_attacking_order - his_attacking_order) ** 2) * params.WRONG_ATTACKING_ORDER_MULT

  return penalty

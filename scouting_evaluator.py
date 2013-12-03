from battle_evaluator import _HoldItemsBonus, _HealEffect
from constants import Point
import global_vars
import map_util
from model.BonusType import BonusType
from model.TrooperType import TrooperType
import params
import util


def EvaluatePosition(context, position):
  benefit_score = _TowardsTheGoalScore(context, position)
  safety_score = _SafetyScore(context, position)
  action_points_score = position.action_points * .1
  if safety_score >= 0:
    return benefit_score + action_points_score
  else:
    return safety_score + action_points_score


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


def _TowardsTheGoalScore(context, position):
  hp_improvement = _HealEffect(context, position) * 1.2
  items_bonus = _HoldItemsBonus(context, position) * .2
  next_corner = global_vars.NextCorner()
  dist = global_vars.distances[next_corner.x][next_corner.y][position.me.xy.x][position.me.xy.y]
  dist_score = 100 - dist
  return hp_improvement + items_bonus + dist_score


def _GetCellDangerScore(context, position):
  move_cost = util.MoveCost(context, position.me.stance)
  if position.action_points >= params.NO_DANGER_IF_N_MOVES_LEFT * move_cost:
    return 0
  xy = position.me.xy
  invisible_enemies = [p for p in global_vars.cell_dominated_by[position.me.stance][xy.x][xy.y]
                       if not context.IsVisible(p, position.me.stance)]
  return len(invisible_enemies)


def _SafetyScore(context, position):
  #sparsity_penalty = _DistFromHerdPenalty(context, position)
  if context.world.move_index == 0 and map_util.SecureOnFirstTurn(context):
    return 0

  cell_danger_score = _GetCellDangerScore(context, position)
  if cell_danger_score > 0:
    return -cell_danger_score * 100
  else:
    return -_AttackingOrderPenalty(context, position)


def _AttackingOrderPenalty(context, position):
  discount = 1 if map_util.RelaxAttackingOrder(context) else 0

  goal = global_vars.NextCorner()
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

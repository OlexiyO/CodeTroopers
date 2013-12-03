import battle_simulator
from constants import Point
import global_vars
from model.BonusType import BonusType
from model.TrooperType import TrooperType
import params
import util

G = None
SHOULD_ASSERT = True

class TurnOrder(object):
  YOURS = 0
  UNKNOWN = 1
  MY = 2


def EvaluatePosition(context, position):
  global SHOULD_ASSERT
  if SHOULD_ASSERT:
    SHOULD_ASSERT = False
    assert _LowHPBonus(context, 1) < params.KILL_EXTRA_PROFIT, _LowHPBonus(context, 1)

  points_scored = _PointsScored(context, position)
  hp_improvement = _HealEffect(context, position) * 1.2
  items_bonus = _HoldItemsBonus(context, position) * .2
  svd_bonus = 0 #_TotalSVDBonus(context, position)
  commander_bonus = 0 #_PositionBonus(context, position)

  min_ap_bonus = max(0, position.action_points - 2) * .1
  prediction_score = battle_simulator.PredictBattle(context, position)
  return points_scored + hp_improvement + commander_bonus + svd_bonus + items_bonus + prediction_score + min_ap_bonus


def _HoldItemsBonus(context, position):
  scores = util.ComputeItemBonuses(context, position.me)
  btypes = [BonusType.MEDIKIT, BonusType.FIELD_RATION, BonusType.GRENADE]
  total = 0
  for bt, score in zip(btypes, scores):
    if position.HasBonus(bt):
      total += score
  return total

@util.TimeMe
def _LowHPBonus(context, hp_left):
  assert params.LOW_LIFE_CUTOFF <= context.game.grenade_collateral_damage
  if hp_left > context.game.grenade_direct_damage:
    return 0
  total = 0
  if hp_left <= params.LOW_LIFE_CUTOFF:
    total += (params.LOW_LIFE_CUTOFF - hp_left) * params.LOW_LIFE_BONUS
  if hp_left <= context.game.grenade_collateral_damage:
    delta = context.game.grenade_collateral_damage - max(hp_left, params.LOW_LIFE_CUTOFF)
    total += delta * params.BELOW_COLLATERAL_GRENADE_BONUS
  if hp_left <= context.game.grenade_direct_damage:
    delta = context.game.grenade_direct_damage - max(hp_left, context.game.grenade_collateral_damage)
    total += delta * params.BELOW_DIRECT_GRENADE_BONUS
  return total


@util.TimeMe
def _PointsScored(context, position):
  total = 0
  for pos, enemy in context.enemies.iteritems():
    old_hp, new_hp = enemy.hitpoints, position.enemies_hp[pos]
    total += old_hp - new_hp
    if new_hp > 0:
      pass  #total += _LowHPBonus(context, new_hp)
    else:
      total += params.KILL_EXTRA_PROFIT
  return total


@util.TimeMe
def _HealEffect(context, position):
  total = 0
  for ally in context.allies.itervalues():
    old_hp = ally.hitpoints
    new_hp = position.allies_hp[ally.type]
    total += (new_hp - old_hp) * params.HEAL_DISCOUNT
    if new_hp == 0:
      total -= params.SELF_KILL_PENALTY

  return total


@util.TimeMe
def _TotalSVDBonus(context, position):
  they_see_us = {}
  if not any(v for v in position.enemies_hp.itervalues()):
    return 0
  attack_promise = 0
  i_can_shoot = False
  they_can_shoot = set()
  for t, hp in enumerate(position.allies_hp):
    if hp is None or hp <= 0:
      continue
    unit = position.GetUnit(t)
    for exy, enemy in context.enemies.iteritems():
      if position.enemies_hp[exy] > 0:
        if util.CanShoot(context, enemy, unit):
          they_can_shoot.add(exy)
        if util.CanSee(context, enemy, unit):
          they_see_us[unit.xy] = 1
        if util.CanShoot(context, unit, enemy):
          i_can_shoot |= (unit.type == position.me.type)
          attack_promise += 1.

  defence_weakness = sum(they_see_us.itervalues())

  if defence_weakness == 0:
    defence_weakness -= 1.

  they_shoot_penalty = sum(util.DPS(context.enemies[xy]) for xy in they_can_shoot)

  if i_can_shoot:
    min_distance_pen = 0
  else:
    D = global_vars.distances[position.me.xy.x][position.me.xy.y]
    min_distance = min(D[exy.x][exy.y] if position.enemies_hp[exy] > 0 else 1000 for exy in context.enemies)
    min_distance_pen = min_distance * params.SVD_DISTANCE_RATIO if min_distance < 100 else 0
  return (attack_promise - defence_weakness) * params.SVD_BONUS_MULT - min_distance_pen - they_shoot_penalty
  # TODO: Remove distance bonus if within shooting range.



def _PositionBonus(context, position):
  count = 0
  ally_units = [(p, u) for p, u in context.allies.iteritems()]
  for p1, u1 in ally_units:
    if u1.type == TrooperType.COMMANDER:
      if p1 == Point(position.me.x, position.me.y):
        p1 = position.me.xy
      for p2, u2 in ally_units:
        if p2 == Point(position.me.x, position.me.y):
          p2 = position.me.xy
        if p2 != p1 and util.Dist(p1, p2) <= context.game.commander_aura_range:
          count += 1
  return count * params.EXTRA_ACTION_POINT_BONUS * context.game.commander_aura_bonus_action_points

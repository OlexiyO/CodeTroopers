import math
import actions
from constants import Point
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
  hp_improvement = _HealEffect(context, position)
  svd_bonus = _PersonalSVDBonus(context, position)
  items_bonus = _HoldItemsBonus(context, position)
  return points_scored + hp_improvement + svd_bonus + items_bonus


def _HoldItemsBonus(context, position):
  return (position.holding_medikit * params.HAS_MEDIKIT_BONUS +
          position.holding_grenade * params.HAS_GRENADE_BONUS +
          position.holding_field_ration* params.HAS_ENERGIZER_BONUS)



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
      total += _LowHPBonus(context, new_hp)
    else:
      total += params.KILL_EXTRA_PROFIT
  return total


@util.TimeMe
def _HealEffect(context, position):
  total = 0
  for pos, ally in context.allies.iteritems():
    old_hp = ally.hitpoints
    new_hp = position.allies_hp[pos] if pos in position.allies_hp else position.allies_hp[position.loc]
    total += (new_hp - old_hp) * params.HEAL_DISCOUNT
    if new_hp == 0:
      total -= params.SELF_KILL_PENALTY

  return total


@util.TimeMe
def _PersonalSVDBonus(context, position):
  if position.allies_hp[position.loc] == 0:
    return 0
  if not any(v for v in position.enemies_hp.itervalues()):
    return 0

  they_see_me = 0
  for exy, enemy in context.enemies.iteritems():
    if position.enemies_hp[exy] > 0:
      they_see_me += util.IsVisible(
        context.world, enemy.vision_range, exy.x, exy.y, enemy.stance, position.loc.x, position.loc.y, position.stance)

  if they_see_me:
    return -params.SVD_BONUS_MULT

  i_see_them = 0
  for exy, enemy in context.enemies.iteritems():
    if position.enemies_hp[exy] > 0:
      i_see_them += util.IsVisible(
        context.world, context.me.vision_range, position.loc.x, position.loc.y, position.stance, exy.x, exy.y, enemy.stance)

  min_distance = min(util.Dist(position.loc, exy) if position.enemies_hp[exy] > 0 else 1000 for exy in context.enemies)
  min_distance_bonus = -min_distance * params.SVD_DISTANCE_RATIO if min_distance < 100 else 0
  return i_see_them + min_distance_bonus


@util.TimeMe
def _TotalSVDBonus(context, position):
  ally_units = {p: u for p, u in context.allies.iteritems()}
  ally_units[position.loc] = ally_units.pop(Point(context.me.x, context.me.y))
  they_see_us = {}
  we_see_them = {}
  if not any(v for v in position.enemies_hp.itervalues()):
    return 0
  for axy, ally in ally_units.iteritems():
    if position.allies_hp[axy] == 0:
      continue
    stance = ally.stance if axy in context.allies else position.stance
    for exy, enemy in context.enemies.iteritems():
      if position.enemies_hp[exy] > 0:
        they_see_us[axy] = util.IsVisible(
          context.world, enemy.vision_range, exy.x, exy.y, enemy.stance, axy.x, axy.y, stance)
        we_see_them[exy] = util.IsVisible(
          context.world, ally.vision_range, axy.x, axy.y, stance, exy.x, exy.y, enemy.stance)

  attack_promise = sum(we_see_them.values())
  defence_weakness = sum(they_see_us.values())
  if attack_promise == 0:
    attack_promise -= 1
  if defence_weakness == 0:
    defence_weakness -= 1
  min_distance = min(util.Dist(position.loc, exy) if position.enemies_hp[exy] > 0 else 1000 for exy in context.enemies)
  min_distance_bonus = -min_distance * params.SVD_DISTANCE_RATIO if min_distance < 100 else 0
  return attack_promise - defence_weakness + min_distance_bonus
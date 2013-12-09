"""How to evaluate battle position."""

import battle_simulator
import constants
from model.BonusType import BonusType
import params
import util


def EvaluatePosition(context, position):
  points_scored = _PointsScored(context, position)
  hp_improvement = _HealEffect(context, position) * 1.2
  items_bonus = _HoldItemsBonus(context, position) * .2
  min_ap_bonus = max(0, position.action_points - 2) * .1
  prediction_score = battle_simulator.PredictBattle(context, position)
  return points_scored + hp_improvement + items_bonus + prediction_score + min_ap_bonus


def _HoldItemsBonus(context, position):
  return sum(util.ComputeBonusProfit(context, position.me, bonus_type)
             for bonus_type in constants.ALL_BONUSES if position.HasBonus(bonus_type))


@util.TimeMe
def _PointsScored(context, position):
  # How many damage we already did.
  total = 0
  for pos, enemy in context.enemies.iteritems():
    old_hp, new_hp = enemy.hitpoints, position.enemies_hp[pos]
    total += old_hp - new_hp
    if new_hp <= 0:
      total += params.KILL_EXTRA_PROFIT
  return total


@util.TimeMe
def _HealEffect(context, position):
  # How much hp we healed.
  total = 0
  for ally in context.allies.itervalues():
    old_hp = ally.hitpoints
    new_hp = position.allies_hp[ally.type]
    total += new_hp - old_hp
    if new_hp == 0:
      total -= params.KILL_EXTRA_PROFIT

  return total

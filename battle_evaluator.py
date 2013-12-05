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
  points_scored = _PointsScored(context, position)
  hp_improvement = _HealEffect(context, position) * 1.2
  items_bonus = _HoldItemsBonus(context, position) * .2
  min_ap_bonus = max(0, position.action_points - 2) * .1
  prediction_score = battle_simulator.PredictBattle(context, position)
  return points_scored + hp_improvement + items_bonus + prediction_score + min_ap_bonus


def _HoldItemsBonus(context, position):
  scores = util.ComputeItemBonuses(context, position.me)
  btypes = [BonusType.MEDIKIT, BonusType.FIELD_RATION, BonusType.GRENADE]
  total = 0
  for bt, score in zip(btypes, scores):
    if position.HasBonus(bt):
      total += score
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

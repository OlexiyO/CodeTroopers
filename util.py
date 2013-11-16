import math
from model.TrooperStance import TrooperStance
import params

def CanShoot(me, enemy, world):
  return world.is_visible(me.shooting_range, me.x, me.y, me.stance, enemy.x, enemy.y, enemy.stance)


def MoveCost(trooper, game):
  if trooper.stance == TrooperStance.STANDING:
    return game.standing_move_cost
  elif trooper.stance == TrooperStance.KNEELING:
    return game.kneeling_move_cost
  else:
    assert trooper.stance == TrooperStance.PRONE
    return game.prone_move_cost


def ShootDamage(trooper, trooper_stance):
  if trooper_stance == TrooperStance.STANDING:
    return trooper.standing_damage
  elif trooper_stance == TrooperStance.KNEELING:
    return trooper.kneeling_damage
  else:
    assert trooper_stance == TrooperStance.PRONE
    return trooper.prone_damage


def ComputeDamage(enemy, dmg):
  assert enemy is not None
  realdmg = min(dmg, enemy.hitpoints)
  return realdmg + params.KILL_EXTRA_PROFIT if realdmg == enemy.hitpoints else realdmg


def CheckType(obj, T):
  assert isinstance(obj, T), 'Type %s, but is %s' % (T, type(obj))


def Dist(pa, pb):
  return math.hypot(pa.x - pb.x, pa.y - pb.y)


def NextCell(pa, pb):
  return abs(pa.x - pb.x) + abs(pa.y - pb.y) == 1


def ReduceHP(hp, dmg):
  return max(0, hp - dmg)
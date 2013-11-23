import math
import os
import datetime
import MyStrategy
from model.TrooperStance import TrooperStance
import params

def CanShoot(me, enemy, world):
  return world.is_visible(me.shooting_range, me.x, me.y, me.stance, enemy.x, enemy.y, enemy.stance)


def CanSee(me, enemy, world):
  return world.is_visible(me.vision_range, me.x, me.y, me.stance, enemy.x, enemy.y, enemy.stance)


def MoveCost(trooper_stance, game):
  if trooper_stance == TrooperStance.STANDING:
    return game.standing_move_cost
  elif trooper_stance == TrooperStance.KNEELING:
    return game.kneeling_move_cost
  else:
    assert trooper_stance == TrooperStance.PRONE
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


TOTAL_TIME = {}
import time

def TimeMe(func):
  def Wrapped(*args, **kwargs):
    x = time.time()
    r = func(*args, **kwargs)
    dt = time.time() - x
    key = func.func_name
    t0 = TOTAL_TIME.get(key, 0)
    TOTAL_TIME[key] = t0 + dt
    return r
  return Wrapped


@TimeMe
def IsVisible(world, max_range, viewer_x, viewer_y, viewer_stance, object_x, object_y, object_stance):
  if math.hypot(object_x - viewer_x, object_y - viewer_y) > max_range:
    return False
  min_stance_index = min(viewer_stance, object_stance)
  cv = min_stance_index + 3 * (object_y + world.height * (object_x + world.width * (viewer_y + world.height * viewer_x)))
  return ord(world.cell_visibilities[cv]) == 1


def GetName(enum_type, field_value):
  for name in dir(enum_type):
    if not name.startswith('_') and getattr(enum_type, name) == field_value:
      return name
  assert False


def SaveDebugDataToDisk():
  dt = datetime.datetime.now().strftime('%m%d_%H%M%S')
  MyStrategy.LOG_DIR = os.path.join('C:/Coding/CodeTroopers/logs', dt)
  os.makedirs(MyStrategy.LOG_DIR)

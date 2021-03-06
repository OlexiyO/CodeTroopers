import os
import datetime
from constants import *
import constants
import global_vars
from model.BonusType import BonusType
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType


def MoveCost(context, trooper_stance):
  game = context.game
  if trooper_stance == TrooperStance.STANDING:
    return game.standing_move_cost
  elif trooper_stance == TrooperStance.KNEELING:
    return game.kneeling_move_cost
  else:
    assert trooper_stance == TrooperStance.PRONE
    return game.prone_move_cost


def ShootDamage(trooper):
  if trooper.stance == TrooperStance.STANDING:
    return trooper.standing_damage
  elif trooper.stance == TrooperStance.KNEELING:
    return trooper.kneeling_damage
  else:
    assert trooper.stance == TrooperStance.PRONE
    return trooper.prone_damage


def NextCell(pa, pb):
  return abs(pa.x - pb.x) + abs(pa.y - pb.y) == 1


TOTAL_TIME = {}
MOVE_TIMES = {}
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
def IsVisible(context, max_range, viewer_x, viewer_y, viewer_stance, object_x, object_y, object_stance):
  # Take original World.IsVisible, and make it faster.
  if (object_x - viewer_x) ** 2 + (object_y - viewer_y) ** 2 > max_range * max_range:
    return False
  min_stance_index = min(viewer_stance, object_stance)
  cv = min_stance_index + 3 * object_y + 60 * object_x + 1800 * viewer_y + 36000 * viewer_x
  return ord(context.world.cell_visibilities[cv]) == 1


def GetName(enum_type, field_value):
  # Print enum numbers in a pretty way ("MEDIC STANDING" instead of "1 2")
  for name in dir(enum_type):
    if not name.startswith('_') and getattr(enum_type, name) == field_value:
      return name
  assert False


def StartSavingDebugDataToDisk():
  dt = datetime.datetime.now().strftime('%m%d_%H%M%S')
  constants.LOG_DIR = os.path.join('C:/Coding/CodeTroopers/logs', dt)
  os.makedirs(constants.LOG_DIR)


def _PrecomputeDistances(context):
  global_vars.distances = Array2D(None)
  for x_ in xrange(X):
    for y_ in xrange(Y):
      if context.IsPassable(Point(x_, y_)):
        if x_ >= X / 2:
          other = global_vars.distances[X - x_ - 1][y_]
          global_vars.distances[x_][y_] = [other[X - i - 1] for i in xrange(X)]
        elif y_ >= Y / 2:
          other = global_vars.distances[x_][Y - y_ - 1]
          global_vars.distances[x_][y_] = [list(reversed(other[i])) for i in xrange(X)]
        else:
          data = Array2D(1000)
          data[x_][y_] = 0
          q = [None] * (X * Y)
          q[0] = Point(x_, y_)
          pos = 0
          lastp = 1
          while pos < lastp:
            p = q[pos]
            pos += 1
            t = data[p.x][p.y] + 1
            for d in ALL_DIRS:
              p1 = PointAndDir(p, d)
              if context.IsPassable(p1) and data[p1.x][p1.y] > t:
                data[p1.x][p1.y] = t
                q[lastp] = p1
                lastp += 1
          global_vars.distances[x_][y_] = data


def HasBonus(trooper, bonus_type):
  if bonus_type == BonusType.FIELD_RATION:
    return trooper.holding_field_ration
  elif bonus_type == BonusType.GRENADE:
    return trooper.holding_grenade
  elif bonus_type == BonusType.MEDIKIT:
    return trooper.holding_medikit
  assert False


def ShootingRange(context, trooper):
  range = trooper.shooting_range
  if trooper.type != TrooperType.SNIPER:
    return range
  range = global_vars.SNIPER_SHOOTING_RANGE
  if trooper.stance == TrooperStance.STANDING:
    return range + context.game.sniper_standing_shooting_range_bonus
  elif trooper.stance == TrooperStance.PRONE:
    return range + context.game.sniper_prone_shooting_range_bonus
  elif trooper.stance == TrooperStance.KNEELING:
    return range + context.game.sniper_kneeling_shooting_range_bonus
  assert False


def VisionDiscount(context, trooper):
  if trooper.type != TrooperType.SNIPER:
    return 0
  elif trooper.stance == TrooperStance.STANDING:
    return context.game.sniper_standing_stealth_bonus
  elif trooper.stance == TrooperStance.PRONE:
    return context.game.sniper_prone_stealth_bonus
  elif trooper.stance == TrooperStance.KNEELING:
    return context.game.sniper_kneeling_stealth_bonus
  assert False


def CanSee(context, who, target):
  if who.type == TrooperType.SCOUT:
    return IsVisible(context, who.vision_range, who.xy.x, who.xy.y, who.stance, target.xy.x, target.xy.y, target.stance)
  else:
    return IsVisible(context, who.vision_range - VisionDiscount(context, target), who.xy.x, who.xy.y,
                     who.stance, target.xy.x, target.xy.y, target.stance)


@TimeMe
def CanShoot(context, who, target):
  return IsVisible(context, ShootingRange(context, who), who.xy.x, who.xy.y, who.stance, target.xy.x, target.xy.y, target.stance)


def Array2D(value, x=X, y=Y):
  array_1d = [value] * y
  return [list(array_1d) for _ in range(x)]


def ComputeBonusProfit(context, trooper, bonus_type):
  # For each bonus: how much profit per action point is it (compared to just shooting).
  G = context.game
  dps = trooper.kneeling_damage / float(trooper.shoot_cost)
  if bonus_type == BonusType.MEDIKIT:
    # We can heal ourselves or someone else -- so compute average of those two things.
    return max(0, .5 * (G.medikit_bonus_hitpoints + G.medikit_heal_self_bonus_hitpoints) - dps * G.medikit_use_cost)
  elif bonus_type == BonusType.FIELD_RATION:
    return max(0, (G.field_ration_bonus_action_points - G.field_ration_eat_cost) * dps)
  else:
    assert bonus_type == BonusType.GRENADE, bonus_type
    return max(0, (G.grenade_direct_damage - G.grenade_throw_cost * dps))


def PrintTrooper(trooper):
  return '%11s (%d, %d) %s' % (GetName(TrooperType, trooper.type), trooper.x, trooper.y, GetName(TrooperStance, trooper.stance))


def PlayerCountFromTeamSize(ts):
  return 2 if ts == 5 else 4


def ManhDist(A, B):
  return global_vars.distances[A.x][A.y][B.x][B.y]


def ClosestEmptyCell(context, to):
  for dist in range(1, 10):
    for dx in range(dist + 1):
      for dy in range(dist + 1 - dx):
        for x in (-dx, dx):
          for y in (-dy, dy):
            p1 = Point(to.x + x, to.y + y)
            if context.CanMoveTo(p1):
              return p1
  return None


def PointAndDir(p, d):
  return Point(p.x + d.x, p.y + d.y)
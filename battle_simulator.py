from collections import namedtuple
from constants import Point, ALL_DIRS, PointAndDir
import global_vars
from model.TrooperStance import TrooperStance
import params
import util


we_shoot_them = None
they_shoot_us = None
they_see_us = None
full_order = None
enemies_xy = None

MY_TURN = 0
ENEMY_TURN = 1


BattleTurn = namedtuple('BattleTurn', ['side', 'round', 'unit'])


class BattleSimulator(object):

  @util.TimeMe
  def __init__(self, context, position):
    self.context = context
    self.position = position
    self.allies_hp = list(position.allies_hp)
    self.enemies_hp = [position.enemies_hp[xy] for xy in enemies_xy]
    my_type = position.me.type
    see_me = False
    global they_see_us
    global we_shoot_them
    global they_shoot_us
    for enemy_index, xy in enumerate(enemies_xy):
      enemy = context.enemies[xy]
      can_see = self.enemies_hp[enemy_index] > 0 and util.CanSee(context, enemy, position.me)
      see_me |= can_see
      they_see_us[enemy_index][my_type] = can_see

    self.i_shoot_them = False

    for enemy_index, xy in enumerate(enemies_xy):
      if see_me:
        enemy = context.enemies[xy]
        can_shoot = util.CanShoot(context, position.me, enemy)
        we_shoot_them[my_type][enemy_index] = can_shoot
        self.i_shoot_them |= can_shoot
        they_shoot_us[enemy_index][my_type] = see_me and util.CanShoot(context, enemy, position.me)
      else:
        they_shoot_us[enemy_index][my_type] = False

  @util.TimeMe
  def MyShot(self, t):
    global we_shoot_them
    if not self.allies_hp[t]:
      return 0
    ally = self.position.GetUnit(t)
    ap = ally.initial_action_points
    num_shots = ap / ally.shoot_cost
    dmg = util.ShootDamage(ally)
    res = 0
    while num_shots > 0:
      score = 0
      ind = 0
      dmg_done = 0
      max_possible = dmg * num_shots
      for n, hp in enumerate(self.enemies_hp):
        if hp > 0 and we_shoot_them[t][n]:
          dmg_done_here = min(max_possible, hp)
          score_here = params.KILL_EXTRA_PROFIT + hp if max_possible >= hp else max_possible
          if score_here > score:
            ind, score, dmg_done = n, score_here, dmg_done_here
      if dmg_done == 0:
        break

      res += score
      self.enemies_hp[ind] -= dmg_done
      num_shots -= (dmg_done + dmg - 1)/ dmg
    return res

  @util.TimeMe
  def EnemyShot(self, enemy_index):
    global we_shoot_them
    if not self.enemies_hp[enemy_index]:
      return 0
    enemy = self.context.enemies[enemies_xy[enemy_index]]
    ap = enemy.initial_action_points
    num_shots = ap / enemy.shoot_cost
    dmg = util.ShootDamage(enemy)
    res = 0
    while num_shots > 0:
      score = 0
      ind = 0
      dmg_done = 0
      max_possible = dmg * num_shots
      for t, hp in enumerate(self.allies_hp):
        if hp > 0 and they_shoot_us[enemy_index][t]:
          dmg_done_here = min(max_possible, hp)
          score_here = params.SELF_KILL_PENALTY + hp if max_possible >= hp else max_possible
          if score_here > score:
            ind, score, dmg_done = t, score_here, dmg_done_here
      if dmg_done == 0:
        break

      res += score
      self.allies_hp[ind] -= dmg_done
      num_shots -= (dmg_done + dmg - 1)/ dmg
    return res

  def SomeEnemySeesUs(self):
    for enemy_index, hp in enumerate(self.enemies_hp):
      if hp > 0 and (any(they_see_us[enemy_index]) or any(they_shoot_us[enemy_index])):
        return True
    return False


@util.TimeMe
def EnemyFights(simulator, context, position):
  global full_order
  enemy_sees_us = simulator.SomeEnemySeesUs()
  gained = 0
  lost = 0
  for turn in full_order:
    if turn.side == MY_TURN:
      gained += params.PREDICTION_DMG_DISCOUNT * simulator.MyShot(turn.unit)
    elif enemy_sees_us:
      lost += simulator.EnemyShot(turn.unit)
  if not simulator.i_shoot_them:
    gained -= global_vars.distances[position.me.xy.x][position.me.xy.y][enemies_xy[0].x][enemies_xy[0].y] * .3
  return gained, lost


@util.TimeMe
def EnemyRuns(simulator, context, position):
  global full_order
  gained = 0
  for turn in full_order:
    if turn.round > 0:
      break
    if turn.side == MY_TURN:
      gained += simulator.MyShot(turn.unit)
    else:
      # This unit runs away. We can't shoot it.
      simulator.enemies_hp[turn.unit] = 0
  if not simulator.i_shoot_them:
    gained -= global_vars.distances[position.me.xy.x][position.me.xy.y][enemies_xy[0].x][enemies_xy[0].y] * .3
  return gained


@util.TimeMe
def SafetyBonus(simulator, context, position):
  suspicious_cells = set(enemies_xy)
  xy = position.me.xy
  for exy in enemies_xy:
    for d in ALL_DIRS:
      p1 = PointAndDir(exy, d)
      if context.IsPassable(p1):
        suspicious_cells.add(p1)

  dangerous_cells = len([p for p in suspicious_cells
                         if util.IsVisible(context, 8, p.x, p.y, TrooperStance.STANDING, xy.x, xy.y, position.me.stance)])
  invisible_enemy_danger = -dangerous_cells / 10.
  they_dont_see_us_bonus = 0 if (simulator.SomeEnemySeesUs() or dangerous_cells > 0) else params.THEY_DONT_SEE_US_BONUS
  return invisible_enemy_danger + they_dont_see_us_bonus


@util.TimeMe
def PredictBattle(context, position):
  simulator = BattleSimulator(context, position)
  ahp, ehp = list(simulator.allies_hp), list(simulator.enemies_hp)
  gained, lost = EnemyFights(simulator, context, position)
  simulator.allies_hp, simulator.enemies_hp = list(ahp), list(ehp)
  gain_if_they_run = EnemyRuns(simulator, context, position)
  simulator.allies_hp, simulator.enemies_hp = list(ahp), list(ehp)
  safety_bonus = SafetyBonus(simulator, context, position)
  return safety_bonus + min(gained - lost * params.HEAL_DISCOUNT, gain_if_they_run)


# What do we store
# full_order: what call and in which order.
# allies_hp = [100, 0, 80, 0, 0] -- value i corresponds to health of my unit of type i.
# enemies_hp = [100, 0, 80, 0, 0] -- value i corresponds to health of enemies unit with index i (position.enemies_hp[i])
# we_shoot_them - whether i-th our unit can shoot j-th their unit
# they_shoot_us - whether i-th their unit can shoot ...
def Precompute(context, position):
  if len(global_vars.UNITS_ORDER) != global_vars.UNITS_IN_GAME:
    order = list(global_vars.UNITS_ORDER)
    for a in context.allies.itervalues():
      if a.type not in order:
        order.append(a.type)
  else:
    order = global_vars.UNITS_ORDER
  global full_order
  global enemies_xy
  enemies_xy = list(context.enemies.iterkeys())
  full_order = []
  start_from = order.index(position.me.type)
  N = global_vars.UNITS_IN_GAME
  E = len(enemies_xy)
  for round in range(params.BATTLE_SIMULATOR_NUM_ROUNDS):
    for n in range(N):
      unit_type = order[(start_from + n) % N]
      if round > 0 or n > 0:
        full_order.append(BattleTurn(MY_TURN, round, unit_type))
      for enemy_index, xy in enumerate(enemies_xy):
        enemy = context.enemies[xy]
        if enemy.type == unit_type:
          full_order.append(BattleTurn(ENEMY_TURN, round, enemy_index))
  global we_shoot_them
  global they_shoot_us
  global they_see_us
  we_shoot_them = util.Array2D(False, N, E)
  they_shoot_us = util.Array2D(False, E, N)
  they_see_us = util.Array2D(False, E, N)

  for ally_type in range(N):
    ally = position.GetUnit(ally_type)
    if ally is not None:
      for enemy_index, xy in enumerate(enemies_xy):
        enemy = context.enemies[xy]
        they_see_us[enemy_index][ally_type] = util.CanSee(context, enemy, ally)

  for ally_type in range(N):
    ally = position.GetUnit(ally_type)
    see_ally = any(they_see_us[ei][ally_type] for ei in range(E))
    if ally is not None and ally.type != position.me.type:
      for enemy_index, xy in enumerate(enemies_xy):
        enemy = context.enemies[xy]
        we_shoot_them[ally_type][enemy_index] = util.CanShoot(context, ally, enemy)
        they_shoot_us[enemy_index][ally_type] = see_ally and util.CanShoot(context, enemy, ally)

import global_vars
from model.TrooperType import TrooperType
import params
import util


class BattleSimulator(object):

  def __init__(self, context, position):
    self.context = context
    self.position = position
    self.enemies = []
    self.enemies_hp = []
    self.orig_enemies_hp = []
    self.allies = []
    self.allies_hp = []
    self.orig_allies_hp = []
    self.score = 0
    self.ally_captain_ind = -1
    self.enemy_captain_ind = -1
    for xy, hp in sorted(position.enemies_hp.iteritems(), key=lambda x: x[1]):
      if hp > 0:
        self.enemies.append(context.enemies[xy])
        self.enemies_hp.append(hp)
        self.orig_enemies_hp.append(hp)
        if context.enemies[xy].type == TrooperType.COMMANDER:
          self.enemy_captain_ind = len(self.enemies) - 1

    for t, hp in sorted(enumerate(position.allies_hp), key=lambda x: x[1]):
      if hp is not None and hp > 0:
        unit = position.GetUnit(t)
        self.allies.append(unit)
        self.allies_hp.append(hp)
        self.orig_allies_hp.append(hp)
        if unit.type == TrooperType.COMMANDER:
          self.ally_captain_ind = len(self.allies) - 1

    #self.we_see_them = [list([False] * len(self.enemies)) for _ in self.allies]
    self.we_shoot_them = [list([False] * len(self.enemies)) for _ in self.allies]
    #self.they_see_us = [list([False] * len(self.allies)) for _ in self.enemies]
    self.they_shoot_us = [list([False] * len(self.allies)) for _ in self.enemies]
    if self.ally_captain_ind != -1:
      capxy = self.allies[self.ally_captain_ind].xy
      self.allies_under_captain = [util.Dist(ally.xy, capxy) <= context.game.commander_aura_range for ally in self.allies]
    else:
      self.allies_under_captain = [False] * len(self.allies)
    if self.enemy_captain_ind != -1:
      capxy = self.enemies[self.enemy_captain_ind].xy
      self.enemies_under_captain = [util.Dist(enemy.xy, capxy) <= context.game.commander_aura_range for enemy in self.enemies]
    else:
      self.enemies_under_captain = [False] * len(self.enemies)

    for i, a in enumerate(self.allies):
      for j, e in enumerate(self.enemies):
        #self.we_see_them[i][j] = util.CanSee(context, a, e)
        self.we_shoot_them[i][j] = util.CanShoot(context, a, e)
        #self.they_see_us[j][i] = util.CanSee(context, e, a)
        self.they_shoot_us[j][i] = util.CanShoot(context, e, a)

  def MyShot(self, t):
    for i, a in enumerate(self.allies):
      if a.type == t:
        if self.allies_hp[i] <= 0:
          return
        ap = a.initial_action_points
        if (0 < self.ally_captain_ind and
            self.ally_captain_ind != i and
            self.allies_under_captain[i] and
            self.allies_hp[self.ally_captain_ind] > 0):
          ap += self.context.game.commander_aura_bonus_action_points
        num_shots = ap / a.shoot_cost
        dmg = util.ShootDamage(a)
        for j, hp in enumerate(self.enemies_hp):
          if hp > 0 and self.we_shoot_them[i][j]:
            cnt = min((hp + dmg - 1) / dmg, num_shots)
            num_shots -= cnt
            self.enemies_hp[j] = max(0, hp - dmg * cnt)

  def EnemyShot(self, t):
    for i, e in enumerate(self.enemies):
      if e.type == t:
        if self.enemies_hp[i] <= 0:
          continue

        ap = e.initial_action_points
        if (0 < self.enemy_captain_ind and
            self.enemy_captain_ind != i and
            self.enemies_hp[self.enemy_captain_ind] > 0 and
            self.enemies_under_captain[i]):
          ap += self.context.game.commander_aura_bonus_action_points
        num_shots = ap / e.shoot_cost
        dmg = util.ShootDamage(e)
        for j, hp in enumerate(self.allies_hp):
          if hp > 0 and self.they_shoot_us[i][j]:
            cnt = min((hp + dmg - 1) / dmg, num_shots)
            num_shots -= cnt
            self.allies_hp[j] = max(0, hp - dmg * cnt)

  def Score(self):
    res = self.score
    for i, hp in enumerate(self.allies_hp):
      if hp == 0:
        res -= params.SELF_KILL_PENALTY
      res += (hp - self.orig_allies_hp[i]) * params.HEAL_DISCOUNT

    for i, hp in enumerate(self.enemies_hp):
      res += self.orig_enemies_hp[i] - hp
      if hp == 0:
        res += params.KILL_EXTRA_PROFIT
    return res


@util.TimeMe
def PredictBattle(context, position):
  if len(global_vars.UNITS_ORDER) != global_vars.UNITS_IN_GAME:
    order = list(global_vars.UNITS_ORDER)
    for a in context.allies.itervalues():
      if a.type not in order:
        order.append(a.type)
  else:
    order = global_vars.UNITS_ORDER
  simulator = BattleSimulator(context, position)
  start_from = order.index(position.me.type)
  N = global_vars.UNITS_IN_GAME
  for move in range(3):
    for n in range(N):
      type_moving = (start_from + n) % N
      if move > 0 or type_moving != start_from:
        simulator.MyShot(order[type_moving])
      simulator.EnemyShot(order[type_moving])
  return simulator.Score()
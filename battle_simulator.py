import global_vars
from model.TrooperType import TrooperType
import params
import util


we_shoot_them = [list([False] * 20) for _ in range(5)]
they_shoot_us = [list([False] * 5) for _ in range(20)]
orig_enemies_hp = [0] * 20
enemies_hp = [0] * 20
orig_allies_hp = [0] * 5
allies_hp = [0] * 5
allies = [None] * 5
enemies = [None] * 20


class BattleSimulator(object):

  @util.TimeMe
  def __init__(self, context, position):
    self.context = context
    self.position = position
    self.score = 0
    self.ally_captain_ind = -1
    self.enemy_captain_ind = -1
    self.ecount = 0
    self.acount = 0
    global orig_allies_hp
    global allies_hp
    global allies
    global orig_enemies_hp
    global enemies_hp
    global enemies
    for xy, hp in sorted(position.enemies_hp.iteritems(), key=lambda x: x[1]):
      if hp > 0:
        enemies[self.ecount] = context.enemies[xy]
        enemies_hp[self.ecount] = hp
        orig_enemies_hp[self.ecount] = hp
        if context.enemies[xy].type == TrooperType.COMMANDER:
          self.enemy_captain_ind = self.ecount
        self.ecount += 1

    for t, hp in sorted(enumerate(position.allies_hp), key=lambda x: x[1]):
      if hp is not None and hp > 0:
        unit = position.GetUnit(t)
        allies[self.acount] = unit
        allies_hp[self.acount] = hp
        orig_allies_hp[self.acount] = hp
        if unit.type == TrooperType.COMMANDER:
          self.ally_captain_ind = self.acount
        self.acount += 1

    #self.we_see_them = [list([False] * len(self.enemies)) for _ in self.allies]
    #self.they_see_us = [list([False] * len(self.allies)) for _ in self.enemies]
    global we_shoot_them
    global they_shoot_us
    if self.ally_captain_ind != -1:
      capxy = allies[self.ally_captain_ind].xy
      self.allies_under_captain = [util.WithinRange(ally.xy, capxy, context.game.commander_aura_range)
                                   for ally in allies[:self.acount]]
    else:
      self.allies_under_captain = [False] * self.acount
    if self.enemy_captain_ind != -1:
      capxy = enemies[self.enemy_captain_ind].xy
      self.enemies_under_captain = [util.WithinRange(enemy.xy, capxy, context.game.commander_aura_range)
                                    for enemy in enemies[:self.ecount]]
    else:
      self.enemies_under_captain = [False] * self.ecount

    for i, a in enumerate(allies[:self.acount]):
      for j, e in enumerate(enemies[:self.ecount]):
        #self.we_see_them[i][j] = util.CanSee(context, a, e)
        we_shoot_them[i][j] = util.CanShoot(context, a, e)
        #self.they_see_us[j][i] = util.CanSee(context, e, a)
        they_shoot_us[j][i] = util.CanShoot(context, e, a)

  @util.TimeMe
  def MyShot(self, t):
    global we_shoot_them
    global allies_hp
    global allies
    global enemies_hp
    for i, a in enumerate(allies[:self.acount]):
      if a.type == t:
        if allies_hp[i] <= 0:
          return
        ap = a.initial_action_points
        if (0 < self.ally_captain_ind and
            self.ally_captain_ind != i and
            self.allies_under_captain[i] and
            allies_hp[self.ally_captain_ind] > 0):
          ap += self.context.game.commander_aura_bonus_action_points
        num_shots = ap / a.shoot_cost
        dmg = util.ShootDamage(a)
        for j, hp in enumerate(enemies_hp[:self.ecount]):
          if hp > 0 and we_shoot_them[i][j]:
            cnt = min((hp + dmg - 1) / dmg, num_shots)
            num_shots -= cnt
            enemies_hp[j] = max(0, hp - dmg * cnt)

  @util.TimeMe
  def EnemyShot(self, t):
    global they_shoot_us
    global allies_hp
    global enemies_hp
    global enemies
    for i, e in enumerate(enemies[:self.ecount]):
      if e.type == t:
        if enemies_hp[i] <= 0:
          continue

        ap = e.initial_action_points
        if (0 < self.enemy_captain_ind and
            self.enemy_captain_ind != i and
            enemies_hp[self.enemy_captain_ind] > 0 and
            self.enemies_under_captain[i]):
          ap += self.context.game.commander_aura_bonus_action_points
        num_shots = ap / e.shoot_cost
        dmg = util.ShootDamage(e)
        for j, hp in enumerate(allies_hp[:self.acount]):
          if hp > 0 and they_shoot_us[i][j]:
            cnt = min((hp + dmg - 1) / dmg, num_shots)
            num_shots -= cnt
            allies_hp[j] = max(0, hp - dmg * cnt)

  @util.TimeMe
  def Score(self):
    global orig_enemies_hp
    global enemies_hp
    global orig_allies_hp
    global allies_hp
    res = self.score
    for i, hp in enumerate(allies_hp[:self.acount]):
      if hp == 0:
        res -= params.SELF_KILL_PENALTY
      res += (hp - orig_allies_hp[i]) * params.HEAL_DISCOUNT

    for i, hp in enumerate(enemies_hp[:self.ecount]):
      res += orig_enemies_hp[i] - hp
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

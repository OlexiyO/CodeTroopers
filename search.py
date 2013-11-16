from collections import namedtuple
import copy
from constants import *
from globals import *
from context import Context
from model.BonusType import BonusType
from model.ActionType import ActionType
from model.Direction import Direction
from model.Move import Move
import params
import util

G = None


class Position(object):

  def __init__(self, context):
    assert isinstance(context, Context)
    me = context.me
    self.allies_hp = {xy: ally.hitpoints for xy, ally in context.allies.iteritems()}
    self.enemies_hp = {xy: enemy.hitpoints for xy, enemy in context.enemies.iteritems()}
    self.bonuses_present = {xy: True for xy in context.world.bonuses.iteritems()}
    self.loc = Point(me.x, me.y)
    self.action_points = me.action_points
    self.stance = me.stance
    self.holding_grenade = me.holding_grenade
    self.holding_medikit = me.holding_medikit
    self.holding_field_ration = me.holding_field_ration

  def TakeBonus(self, bonus_type):
    if G.context.bonuses[self.loc].type == bonus_type and self.bonuses_present[self.loc]:
      self.bonuses_present[self.loc] = False
      return True
    return False


def CopyPosition(other):
  return copy.deepcopy(other)


class Action(object):

  def Allowed(self, position):
    return position.action_points >= self._ActionCost() and self._IsPossible(position)

  def Apply(self, position):
    raise NotImplementedError

  def SetMove(self, move):
    raise NotImplementedError

  def _ActionCost(self):
    raise NotImplementedError

  def _IsPossible(self, position):
    raise NotImplementedError

  def _CopyWithoutActionPoints(self, position):
    res = CopyPosition(position)
    res.action_points -= self._ActionCost()
    assert res.action_points >= 0
    return


class NoneAction(Action):

  def _IsPossible(self, position):
    return True

  def Apply(self, position):
    return position

  def SetMove(self, move):
    move.action = ActionType.END_TURN

  def _ActionCost(self):
    return 0


class MedikitYourself(Action):

  def _IsPossible(self, position):
    return position.holding_medikit and position.hp < 100

  def _ActionCost(self):
    return G.game.medikit_use_cost

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    res.allies_hp[res.loc] = max(100, res.allies_hp[res.loc] + G.game.medikit_heal_self_bonus_hitpoints)
    res.holding_medikit = position.TakeBonus(BonusType.MEDIKIT)
    return res

  def SetMove(self, move):
    move.action = ActionType.USE_MEDIKIT
    move.direction = Direction.CURRENT_POINT


class Walk(Action):
  def __init__(self, where):
    self.where = where

  def _IsPossible(self, position):
    assert util.NextCell(position.loc, self.where), '%s and %s' % (position.loc, self.where)
    if G.context.IsPassable(self.where):
      return False
    for p, ally in G.context.allies.iteritems():
      if p == self.where and position.allies_hp[p]:
        return False
    for p, enemy in G.context.enemies.iteritems():
      if p == self.where and position.enemies_hp[p]:
        return False
    return True

  def _ActionCost(self):
    return util.MoveCost(G.me, G.game)

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    res.loc = self.where
    return res

  def SetMove(self, move):
    move.action = ActionType.MOVE
    move.x, move.y = self.where.x, self.where.y


class Shoot(Action):
  def __init__(self, where):
    self.where = where

  def _IsPossible(self, position):
    enemy = G.context.enemies[self.where]
    return (position.enemies_hp[self.where] > 0 and
            position.action_points >= G.me.shoot_cost and
            G.world.is_visible(G.me.shooting_range, position.loc.x, position.loc.y, position.stance,
                               enemy.x, enemy.y, enemy.stance))

  def _ActionCost(self):
    return G.me.shoot_cost

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    max_dmg = util.ShootDamage(G.me, position.stance)
    res.enemies_hp[self.where] = max(0, res.enemies_hp[self.where] - max_dmg)
    return res

  def SetMove(self, move):
    move.action = ActionType.SHOOT
    move.x, move.y = self.where.x, self.where.y


class ThrowGrenade(Action):

  def __init__(self, where):
    self.where = where

  def _ActionCost(self):
    return G.game.grenade_throw_cost

  def _IsPossible(self, position):
    return position.holding_grenade and util.Dist(self.where, position.loc) <= G.game.grenade_throw_range

  def SetMove(self, move):
     move.action = ActionType.THROW_GRENADE
     move.x = self.where.x
     move.y = self.where.y

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    if res.loc == self.where:
      res.hp = util.ReduceHP(res.hp, G.game.grenade_direct_damage)
    elif util.NextCell(res.loc, self.where):
      res.hp = util.ReduceHP(res.hp, G.game.grenade_collateral_damage)

    for p in G.context.enemies:
      if p == self.where:
        res.enemies_hp[p] = util.ReduceHP(res.enemies_hp[p], G.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        res.enemies_hp[p] = util.ReduceHP(res.enemies_hp[p], G.game.grenade_direct_damage)
    for p in G.context.allies:
      if p == self.where:
        res.allies_hp[p] = util.ReduceHP(res.allies_hp[p], G.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        res.allies_hp[p] = util.ReduceHP(res.allies_hp[p], G.game.grenade_direct_damage)


    res.holding_grenade = position.TakeBonus(BonusType.GRENADE)
    return res


class Searcher(object):
  def DoSearch(self, context):
    global G
    G.game = context.game
    G.world = context.world
    G.me = context.me
    G.context = context
    self.q = [(Position(context), None)]
    self.bestScore, self.bestAction = EvaluatePosition(self.q[0][0]), NoneAction()
    self._Search()
    G = None
    return self.bestAction

  def _Search(self):
    index = 0
    while index < len(self.q):
      pos, first_action = self.q[index]
      if index > 0:
        score = EvaluatePosition(pos)
        if score > self.bestScore:
          self.bestScore, self.bestAction = score, first_action
      index += 1
      allowed_actions = []
      allowed_actions.append(MedikitYourself())
      for xy in G.context.enemies:
        allowed_actions.append(Shoot(xy))

      for act in allowed_actions:
        if act.Allowed(pos):
          self.q.append((act.Apply(pos), first_action if index > 0 else act))


def EvaluatePosition(position):
  hp_diff = sum(position.allies_hp.itervalues()) - sum(position.enemies_hp.itervalues())
  our_dead = len([x for x in position.allies_hp.itervalues() if x == 0])
  opp_dead = len([x for x in position.enemies_hp.itervalues() if x == 0])
  return hp_diff + (our_dead - opp_dead) * params.KILL_EXTRA_PROFIT
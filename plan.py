from constants import *
from model.ActionType import ActionType
from model.Direction import Direction
import params
import util

class Plan(object):

  def IsBetter(self, other):
    if other.GetProfit() != self.GetProfit():
      return self.GetProfit() > other.GetProfit()
    return self.GetCost() < other.GetCost()

  def __init__(self, context):
    self.context = context
    self.me = context.me

  def SetNextStep(self, move):
    raise NotImplementedError

  def Compute(self):
    raise NotImplementedError

  def IsPossible(self):
    raise NotImplementedError

  def GetProfit(self):
    raise NotImplementedError

  def GetCost(self):
    raise NotImplementedError

# TODO: Among different enemies, pick ones with the most damage.
# TODO: Among different enemies, pick ones who will move next.

class ShootDirect(Plan):

  def __init__(self, context, where):
    super(ShootDirect, self).__init__(context)
    self.where = where
    self.enemy = self.context.GetEnemyAt(self.where)
    assert self.enemy is not None  # Still can't shoot at an empty slot

  def IsPossible(self):
    me = self.context.me
    return (me.action_points >= me.shoot_cost and
            util.CanShoot(me, self.enemy, self.context.world))

  def SetNextStep(self, move):
    move.action = ActionType.SHOOT
    move.x = self.where.x
    move.y = self.where.y

  def GetProfit(self):
    return util.ComputeDamage(self.enemy, util.ShootDamage(self.context.me))

  def GetCost(self):
    return self.me.shoot_cost


class HealYourself(Plan):

  def IsPossible(self):
    me = self.context.me
    return (me.action_points >= self.context.game.medikit_use_cost and
            me.holding_medikit)

  def SetNextStep(self, move):
    move.action = ActionType.USE_MEDIKIT
    move.direction = Direction.CURRENT_POINT

  def GetProfit(self):
    return (min(self.context.game.medikit_heal_self_bonus_hitpoints, 100 - self.me.hitpoints) - 10) * params.HEAL_DISCOUNT

  def GetCost(self):
    # Used medikit
    return self.context.me.medikit_use_cost + .5


class ThrowGrenade(Plan):

  def __init__(self, context, where):
    super(ThrowGrenade, self).__init__(context)
    self.where = where

  def IsPossible(self):
    me = self.context.me
    game = self.context.game
    return (
        me.holding_grenade and
        me.action_points >= game.grenade_throw_cost and
        me.get_distance_to(self.where.x, self.where.y) <= game.grenade_throw_range)

  def SetNextStep(self, move):
    move.action = ActionType.THROW_GRENADE
    move.x = self.where.x
    move.y = self.where.y

  def GetProfit(self):
    # TODO: Account for damage to my own units.
    total = 0
    game = self.context.game
    enemy = self.context.GetEnemyAt(self.where)
    if enemy is not None:
      total += util.ComputeDamage(enemy, game.grenade_direct_damage)
    elif self.context.CanHaveHiddenEnemy(self.where):
      total += game.grenade_direct_damage * params.HIDDEN_NEIGHBOR_RATIO
    for d in ALL_DIRS:
      p1 = Point(x=self.where.x + d.x, y=self.where.y + d.y)
      enemy = self.context.GetEnemyAt(p1)
      if enemy is not None:
        total += util.ComputeDamage(enemy, game.grenade_collateral_damage)
      elif self.context.CanHaveHiddenEnemy(p1):
        total += game.grenade_collateral_damage * params.HIDDEN_NEIGHBOR_RATIO
    return total

  def GetCost(self):
    return self.context.game.grenade_throw_cost + .5  # We throw away grenade.

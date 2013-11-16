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
    return util.ComputeDamage(self.enemy, util.ShootDamage(self.context.me, self.context.me.stance))

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

  def _GrenadeDamageAt(self, where, dmg):
    if where in self.context.enemies:
      return  util.ComputeDamage(self.context.enemies[where], dmg)
    elif where in self.context.allies:
      return -util.ComputeDamage(self.context.allies[where], dmg)
    elif self.context.CanHaveHiddenEnemy(where):
      return dmg * params.HIDDEN_NEIGHBOR_RATIO
    else:
      return 0

  def GetProfit(self):
    game = self.context.game
    total = self._GrenadeDamageAt(self.where, game.grenade_direct_damage)
    for d in ALL_DIRS:
      p1 = Point(x=self.where.x + d.x, y=self.where.y + d.y)
      total += self._GrenadeDamageAt(p1, game.grenade_collateral_damage)
    return total

  def GetCost(self):
    return self.context.game.grenade_throw_cost + .5  # We throw away grenade.

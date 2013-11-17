import copy
from constants import *
from context import Context
from model.BonusType import BonusType
from model.ActionType import ActionType
from model.Direction import Direction
import util


class Storage(object):
  pass

context = None


def MaybePickupBonus(pos, context):
  if not pos.bonuses_present.get(pos.loc, False):
    return
  btype = context.bonuses[pos.loc].type
  if btype == BonusType.GRENADE and not pos.holding_grenade:
    pos.holding_grenade = True
    pos.bonuses_present[pos.loc] = False
  elif btype == BonusType.MEDIKIT and not pos.holding_medikit:
    pos.holding_medikit = True
    pos.bonuses_present[pos.loc] = False
  elif btype == BonusType.FIELD_RATION and not pos.holding_field_ration:
    pos.holding_field_ration = True
    pos.bonuses_present[pos.loc] = False


class Position(object):

  def __init__(self, context):
    assert isinstance(context, Context)
    me = context.me
    self.allies_hp = {xy: ally.hitpoints for xy, ally in context.allies.iteritems()}
    self.enemies_hp = {xy: enemy.hitpoints for xy, enemy in context.enemies.iteritems()}
    self.bonuses_present = {p: True for p in context.bonuses}
    self.loc = Point(me.x, me.y)
    self.action_points = me.action_points
    self.stance = me.stance
    self.holding_grenade = me.holding_grenade
    self.holding_medikit = me.holding_medikit
    self.holding_field_ration = me.holding_field_ration


@util.TimeMe
def CopyPosition(other):
  return copy.deepcopy(other)


class Action(object):

  def __init__(self, context):
    self.context = context

  def Allowed(self, position):
    return (position.action_points >= self._ActionCost()) and self._IsPossible(position)

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
    if res.action_points < 0:
      x = self.Allowed(position)
      print x
      assert res.action_points >= 0, res.action_points
    return res


class NoneAction(Action):

  def _IsPossible(self, position):
    return True

  def Apply(self, position):
    return position

  def SetMove(self, move):
    move.action = ActionType.END_TURN

  def _ActionCost(self):
    return 0


class Energizer(Action):

  def _IsPossible(self, position):
    return position.holding_field_ration

  def _ActionCost(self):
    return self.context.game.field_ration_eat_cost

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    res.action_points = min(res.action_points + self.context.game.field_ration_bonus_action_points,
                            self.context.me.initial_action_points)
    res.holding_field_ration = False
    MaybePickupBonus(res, context)
    return res

  def SetMove(self, move):
    move.action = ActionType.EAT_FIELD_RATION
    move.direction = Direction.CURRENT_POINT


class MedikitYourself(Action):

  def _IsPossible(self, position):
    return position.holding_medikit and position.allies_hp[position.loc] < 100

  def _ActionCost(self):
    return self.context.game.medikit_use_cost

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    res.allies_hp[res.loc] = max(100, res.allies_hp[res.loc] + self.context.game.medikit_heal_self_bonus_hitpoints)
    res.holding_medikit = False
    MaybePickupBonus(res, context)
    return res

  def SetMove(self, move):
    move.action = ActionType.USE_MEDIKIT
    move.direction = Direction.CURRENT_POINT


class Walk(Action):
  def __init__(self, context, where):
    super(Walk, self).__init__(context)
    self.where = where

  def _IsPossible(self, position):
    assert util.NextCell(position.loc, self.where), '%s and %s' % (position.loc, self.where)
    if not self.context.IsPassable(self.where):
      return False
    for p, hp in position.allies_hp.iteritems():
      if p == self.where and hp > 0:
        return False
    for p, hp in position.enemies_hp.iteritems():
      if p == self.where and hp > 0:
        return False
    return True

  def _ActionCost(self):
    return util.MoveCost(self.context.me, self.context.game)

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    res.loc = self.where
    res.allies_hp[res.loc] = res.allies_hp.pop(position.loc)
    MaybePickupBonus(res, context)
    return res

  def SetMove(self, move):
    move.action = ActionType.MOVE
    move.x, move.y = self.where.x, self.where.y


class Shoot(Action):
  def __init__(self, context, where):
    super(Shoot, self).__init__(context)
    self.where = where

  def _IsPossible(self, position):
    enemy = self.context.enemies[self.where]
    return (position.enemies_hp[self.where] > 0 and
            util.IsVisible(self.context.world, self.context.me.shooting_range, position.loc.x, position.loc.y, position.stance,
                           enemy.x, enemy.y, enemy.stance))

  def _ActionCost(self):
    return self.context.me.shoot_cost

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)
    max_dmg = util.ShootDamage(self.context.me, position.stance)
    res.enemies_hp[self.where] = max(0, res.enemies_hp[self.where] - max_dmg)
    return res

  def SetMove(self, move):
    move.action = ActionType.SHOOT
    move.x, move.y = self.where.x, self.where.y


class ThrowGrenade(Action):
  def __init__(self, context, where):
    super(ThrowGrenade, self).__init__(context)
    self.where = where

  def _ActionCost(self):
    return self.context.game.grenade_throw_cost

  def _IsPossible(self, position):
    return position.holding_grenade and util.Dist(self.where, position.loc) <= self.context.game.grenade_throw_range

  def SetMove(self, move):
     move.action = ActionType.THROW_GRENADE
     move.x = self.where.x
     move.y = self.where.y

  def Apply(self, position):
    res = self._CopyWithoutActionPoints(position)

    for p in self.context.enemies:
      if p == self.where:
        res.enemies_hp[p] = util.ReduceHP(res.enemies_hp[p], self.context.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        res.enemies_hp[p] = util.ReduceHP(res.enemies_hp[p], self.context.game.grenade_direct_damage)
    for p in self.context.allies:
      if p == self.where:
        res.allies_hp[p] = util.ReduceHP(res.allies_hp[p], self.context.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        res.allies_hp[p] = util.ReduceHP(res.allies_hp[p], self.context.game.grenade_direct_damage)

    res.holding_grenade = False
    MaybePickupBonus(res, context)
    return res

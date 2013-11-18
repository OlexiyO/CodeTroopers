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

  def HasBonus(self, btype):
    if btype == BonusType.GRENADE:
      return self.holding_grenade
    elif btype == BonusType.MEDIKIT:
      return self.holding_medikit
    elif btype == BonusType.FIELD_RATION:
      return self.holding_field_ration
    else:
      assert False, 'Unknown bonus type %d' % btype


class Action(object):

  def __init__(self, context):
    self.context = context

  @util.TimeMe
  def Allowed(self, position):
    return (position.action_points >= self._ActionCost()) and self._IsPossible(position)

  @util.TimeMe
  def Apply(self, position):
    return self._Apply(position)

  def _Apply(self, position):
    raise NotImplementedError

  @util.TimeMe
  def Undo(self, position, info):
    self._Undo(position, info)

  def _Undo(self, position, info):
    raise NotImplementedError

  def SetMove(self, move):
    raise NotImplementedError

  def _ActionCost(self):
    raise NotImplementedError

  def _IsPossible(self, position):
    raise NotImplementedError

  @util.TimeMe
  def _SubtractActionPoints(self, position):
    position.action_points -= self._ActionCost()
    if position.action_points < 0:
      x = self.Allowed(position)
      print x
      assert position.action_points >= 0, position.action_points


class NoneAction(Action):

  def _IsPossible(self, position):
    return True

  def _Apply(self, position):
    return None

  def Revert(self, position):
    pass

  def SetMove(self, move):
    move.action = ActionType.END_TURN

  def _ActionCost(self):
    return 0


class Energizer(Action):

  def _IsPossible(self, position):
    return position.holding_field_ration

  def _ActionCost(self):
    return self.context.game.field_ration_eat_cost

  def _Apply(self, position):
    ap = position.action_points
    bonuses = dict(position.bonuses_present.iteritems())
    self._SubtractActionPoints(position)
    position.action_points = min(position.action_points + self.context.game.field_ration_bonus_action_points,
                                 self.context.me.initial_action_points)
    position.holding_field_ration = False
    MaybePickupBonus(position, context)
    return ap, bonuses

  def _Undo(self, position, info):
    position.holding_field_ration = True
    position.action_points, position.bonuses_present = info

  def SetMove(self, move):
    move.action = ActionType.EAT_FIELD_RATION
    move.direction = Direction.CURRENT_POINT


class Medikit(Action):

  def __init__(self, context, where):
    super(Medikit, self).__init__(context)
    self.where = where
    self.target = self.context.allies.get(self.where, context.me)

  def _IsPossible(self, position):
    if position.loc != self.where:
      assert util.NextCell(position.loc, self.where), '%s and %s' % (position.loc, self.where)
      assert self.where in self.context.allies
    assert self.where in position.allies_hp
    return position.holding_medikit and position.allies_hp[self.where] < self.target.maximal_hitpoints

  def _ActionCost(self):
    return self.context.game.medikit_use_cost

  def _Apply(self, position):
    ap = position.action_points
    hp = dict(position.allies_hp.iteritems())
    bonuses = dict(position.bonuses_present.iteritems())
    self._SubtractActionPoints(position)
    heal_amount = (self.context.game.medikit_heal_self_bonus_hitpoints
                   if self.where == position.loc else
                   self.context.game.medikit_bonus_hitpoints)
    position.allies_hp[position.loc] = max(
      self.target.maximal_hitpoints, position.allies_hp[position.loc] + heal_amount)
    position.holding_medikit = False
    MaybePickupBonus(position, context)
    return ap, hp, bonuses

  def _Undo(self, position, info):
    position.holding_medikit = True
    position.action_points, position.allies_hp, position.bonuses_present = info

  def SetMove(self, move):
    move.action = ActionType.USE_MEDIKIT
    move.x, move.y = self.where.x, self.where.y


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

  def _Apply(self, position):
    ap = position.action_points
    hp = dict(position.allies_hp.iteritems())
    bonuses = dict(position.bonuses_present.iteritems())
    old_loc = position.loc
    what_i_have = position.holding_field_ration, position.holding_grenade, position.holding_medikit

    self._SubtractActionPoints(position)
    position.loc = self.where
    position.allies_hp[position.loc] = position.allies_hp.pop(old_loc)
    MaybePickupBonus(position, context)
    return ap, hp, bonuses, old_loc, what_i_have

  def _Undo(self, position, info):
    position.action_points, position.allies_hp, position.bonuses_present, position.loc, what_i_have = info
    position.holding_field_ration, position.holding_grenade, position.holding_medikit = what_i_have

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

  def _Apply(self, position):
    ap = position.action_points
    ehp = dict(position.enemies_hp.iteritems())

    self._SubtractActionPoints(position)
    max_dmg = util.ShootDamage(self.context.me, position.stance)
    position.enemies_hp[self.where] = max(0, position.enemies_hp[self.where] - max_dmg)
    return ap, ehp

  def _Undo(self, position, info):
    position.action_points, position.enemies_hp = info

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

  def _Apply(self, position):
    ap = position.action_points
    hp = dict(position.allies_hp.iteritems())
    ehp = dict(position.enemies_hp.iteritems())
    bonuses = dict(position.bonuses_present.iteritems())

    self._SubtractActionPoints(position)

    for p in self.context.enemies:
      if p == self.where:
        position.enemies_hp[p] = util.ReduceHP(position.enemies_hp[p], self.context.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        position.enemies_hp[p] = util.ReduceHP(position.enemies_hp[p], self.context.game.grenade_direct_damage)
    for p in self.context.allies:
      if p == self.where:
        position.allies_hp[p] = util.ReduceHP(position.allies_hp[p], self.context.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        position.allies_hp[p] = util.ReduceHP(position.allies_hp[p], self.context.game.grenade_direct_damage)

    position.holding_grenade = False
    MaybePickupBonus(position, context)
    return ap, hp, ehp, bonuses

  def _Undo(self, position, info):
    self.holding_grenade = True
    position.action_points, position.allies_hp, position.enemies_hp, position.bonuses_present = info
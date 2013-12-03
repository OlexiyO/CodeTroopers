import copy
from constants import TOTAL_UNIT_TYPES
from context import Context
from model.BonusType import BonusType
from model.ActionType import ActionType
from model.Direction import Direction
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
import util


class Storage(object):
  pass


def MaybePickupBonus(pos, context):
  loc = pos.me.xy
  if not pos.bonuses_present.get(loc, False):
    return
  btype = context.bonuses[loc].type
  if btype == BonusType.GRENADE and not pos.holding_grenade:
    pos.holding_grenade = True
    pos.bonuses_present[loc] = False
  elif btype == BonusType.MEDIKIT and not pos.holding_medikit:
    pos.holding_medikit = True
    pos.bonuses_present[loc] = False
  elif btype == BonusType.FIELD_RATION and not pos.holding_field_ration:
    pos.holding_field_ration = True
    pos.bonuses_present[loc] = False


class MeError(object):
  pass


class Position(object):

  def __init__(self, context):
    assert isinstance(context, Context)
    me = context.me
    self.me = copy.deepcopy(context.me)
    self.me.x = MeError
    self.me.y = MeError
    self.allies_hp = [None] * TOTAL_UNIT_TYPES
    self.allies_by_type = [None] * TOTAL_UNIT_TYPES
    for xy, ally in context.allies.iteritems():
      t = ally.type
      self.allies_by_type[t] = ally
      self.allies_hp[t] = ally.hitpoints
    self.allies_by_type[me.type] = None
    self.enemies_hp = {xy: enemy.hitpoints for xy, enemy in context.enemies.iteritems()}
    self.bonuses_present = {p: True for p in context.bonuses}
    self.action_points = me.action_points
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

  @util.TimeMe
  def GetUnit(self, utype):
    if utype == self.me.type:
      return self.me
    else:
      #assert self.allies_by_type[utype] is not None
      return self.allies_by_type[utype]


class Action(object):

  def __init__(self, context):
    self.context = context

  def __repr__(self):
    good_items = {name: getattr(self, name) for name in dir(self) if name in ['where', 'who']}
    return '%s %s' % (type(self).__name__, good_items)

  @util.TimeMe
  def Allowed(self, position):
    return (position.action_points >= self._ActionCost(position) and
            position.allies_hp[position.me.type] > 0 and
            self._IsPossible(position))

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

  def SetMove(self, position, move):
    raise NotImplementedError

  def _ActionCost(self, position):
    raise NotImplementedError

  def _IsPossible(self, position):
    raise NotImplementedError

  @util.TimeMe
  def _SubtractActionPoints(self, position):
    cost = self._ActionCost(position)
    if position.action_points < cost:
      x = self.Allowed(position)
      print x
      assert position.action_points >= cost, (position.action_points, cost)
    position.action_points -= cost


class NoneAction(Action):

  def _IsPossible(self, position):
    return True

  def _Apply(self, position):
    return None

  def Revert(self, position):
    pass

  def SetMove(self, position, move):
    move.action = ActionType.END_TURN

  def _ActionCost(self, position):
    return 0


class Energizer(Action):

  def _IsPossible(self, position):
    return position.holding_field_ration

  def _ActionCost(self, position):
    return self.context.game.field_ration_eat_cost

  def _Apply(self, position):
    ap = position.action_points
    bonuses = dict(position.bonuses_present.iteritems())
    position.holding_field_ration = False

    self._SubtractActionPoints(position)
    position.action_points = min(position.action_points + self.context.game.field_ration_bonus_action_points,
                                 position.me.initial_action_points)
    MaybePickupBonus(position, self.context)
    return ap, bonuses

  def _Undo(self, position, info):
    position.holding_field_ration = True
    position.action_points, position.bonuses_present = info

  def SetMove(self, position, move):
    move.action = ActionType.EAT_FIELD_RATION
    move.direction = Direction.CURRENT_POINT


class FieldMedicHeal(Action):
  def __init__(self, context, who):
    super(FieldMedicHeal, self).__init__(context)
    self.who = who

  def _IsPossible(self, position):
    if position.me.type != TrooperType.FIELD_MEDIC:
      return False
    target = position.GetUnit(self.who)
    loc = position.me.xy
    if loc != target.xy and not util.NextCell(loc, target.xy):
      return False
    return 0 < position.allies_hp[self.who] < target.maximal_hitpoints

  def _ActionCost(self, position):
    return self.context.game.field_medic_heal_cost

  def _Apply(self, position):
    ap = position.action_points
    target = position.GetUnit(self.who)
    self._SubtractActionPoints(position)
    heal_amount = (self.context.game.field_medic_heal_self_bonus_hitpoints
                   if self.who == position.me.type else
                   self.context.game.field_medic_heal_bonus_hitpoints)
    heal_amount = min(heal_amount, target.maximal_hitpoints - position.allies_hp[self.who])
    position.allies_hp[self.who] += heal_amount
    return ap, heal_amount

  def _Undo(self, position, info):
    position.action_points, heal_amount = info
    position.allies_hp[self.who] -= heal_amount

  def SetMove(self, position, move):
    move.action = ActionType.HEAL
    target = position.GetUnit(self.who)
    move.x, move.y = target.xy.x, target.xy.y


class UseMedikit(Action):
  def __init__(self, context, who):
    super(UseMedikit, self).__init__(context)
    self.who = who

  def _IsPossible(self, position):
    target = position.GetUnit(self.who)
    loc = position.me.xy
    if loc != target.xy and not util.NextCell(loc, target.xy):
      return False

    return position.holding_medikit and 0 < position.allies_hp[self.who] < target.maximal_hitpoints

  def _ActionCost(self, position):
    return self.context.game.medikit_use_cost

  def _Apply(self, position):
    ap = position.action_points
    bonuses = dict(position.bonuses_present.iteritems())
    position.holding_medikit = False

    target = position.GetUnit(self.who)
    self._SubtractActionPoints(position)
    heal_amount = (self.context.game.medikit_heal_self_bonus_hitpoints
                   if self.who == position.me.type else
                   self.context.game.medikit_bonus_hitpoints)
    heal_amount = min(heal_amount, target.maximal_hitpoints - position.allies_hp[self.who])
    position.allies_hp[self.who] += heal_amount
    MaybePickupBonus(position, self.context)
    return ap, heal_amount, bonuses

  def _Undo(self, position, info):
    position.holding_medikit = True
    position.action_points, heal_amount, position.bonuses_present = info
    position.allies_hp[self.who] -= heal_amount


  def SetMove(self, position, move):
    move.action = ActionType.USE_MEDIKIT
    target = position.GetUnit(self.who)
    move.x, move.y = target.xy.x, target.xy.y


class Walk(Action):
  def __init__(self, context, where):
    super(Walk, self).__init__(context)
    self.where = where

  def _IsPossible(self, position):
    assert util.NextCell(position.me.xy, self.where), '%s and %s' % (position.me.xy, self.where)
    if not self.context.IsPassable(self.where):
      return False
    for p, hp in position.enemies_hp.iteritems():
      if p == self.where and hp > 0:
        return False
    for t, ally in enumerate(position.allies_by_type):
      if ally is not None and ally.xy == self.where and position.allies_hp[t] > 0:
        return False
    return True

  def _ActionCost(self, position):
    return util.MoveCost(self.context, position.me.stance)

  def _Apply(self, position):
    ap = position.action_points
    bonuses = dict(position.bonuses_present.iteritems())
    old_loc = position.me.xy
    what_i_have = position.holding_field_ration, position.holding_grenade, position.holding_medikit

    self._SubtractActionPoints(position)
    position.me.xy = self.where
    MaybePickupBonus(position, self.context)
    return ap, bonuses, old_loc, what_i_have

  def _Undo(self, position, info):
    position.action_points, position.bonuses_present, position.me.xy, what_i_have = info
    position.holding_field_ration, position.holding_grenade, position.holding_medikit = what_i_have

  def SetMove(self, position, move):
    move.action = ActionType.MOVE
    move.x, move.y = self.where.x, self.where.y


class Shoot(Action):
  def __init__(self, context, where):
    super(Shoot, self).__init__(context)
    self.where = where

  def _IsPossible(self, position):
    enemy = self.context.enemies[self.where]
    return (position.enemies_hp[self.where] > 0 and
            util.IsVisible(self.context, util.ShootingRange(self.context, position.me),
                           position.me.xy.x, position.me.xy.y, position.me.stance,
                           enemy.x, enemy.y, enemy.stance))

  def _ActionCost(self, position):
    return position.me.shoot_cost

  def _Apply(self, position):
    ap = position.action_points
    ehp = dict(position.enemies_hp.iteritems())

    self._SubtractActionPoints(position)
    max_dmg = util.ShootDamage(position.me)
    position.enemies_hp[self.where] = max(0, position.enemies_hp[self.where] - max_dmg)
    return ap, ehp

  def _Undo(self, position, info):
    position.action_points, position.enemies_hp = info

  def SetMove(self, position, move):
    move.action = ActionType.SHOOT
    move.x, move.y = self.where.x, self.where.y


class ThrowGrenade(Action):
  def __init__(self, context, where):
    super(ThrowGrenade, self).__init__(context)
    self.where = where

  def _ActionCost(self, position):
    return self.context.game.grenade_throw_cost

  def _IsPossible(self, position):
    return position.holding_grenade and util.WithinRange(self.where, position.me.xy, self.context.game.grenade_throw_range)

  def SetMove(self, position, move):
     move.action = ActionType.THROW_GRENADE
     move.x = self.where.x
     move.y = self.where.y

  def _Apply(self, position):
    ap = position.action_points
    hp = list(position.allies_hp)
    ehp = dict(position.enemies_hp.iteritems())
    bonuses = dict(position.bonuses_present.iteritems())
    position.holding_grenade = False

    self._SubtractActionPoints(position)

    for p in self.context.enemies:
      if p == self.where:
        position.enemies_hp[p] = util.ReduceHP(position.enemies_hp[p], self.context.game.grenade_direct_damage)
      elif util.NextCell(p, self.where):
        position.enemies_hp[p] = util.ReduceHP(position.enemies_hp[p], self.context.game.grenade_direct_damage)
    for t, ally_hp in enumerate(position.allies_hp):
      if ally_hp is None:
        continue
      xy = position.GetUnit(t).xy
      if xy == self.where:
        position.allies_hp[t] = util.ReduceHP(position.allies_hp[t], self.context.game.grenade_direct_damage)
      elif util.NextCell(xy, self.where):
        position.allies_hp[t] = util.ReduceHP(position.allies_hp[t], self.context.game.grenade_direct_damage)

    MaybePickupBonus(position, self.context)
    return ap, hp, ehp, bonuses

  def _Undo(self, position, info):
    position.holding_grenade = True
    position.action_points, position.allies_hp, position.enemies_hp, position.bonuses_present = info


class RaiseStance(Action):
  def _IsPossible(self, position):
    return position.me.stance != TrooperStance.STANDING

  def _ActionCost(self, position):
    return self.context.game.stance_change_cost

  def _Apply(self, position):
    ap = position.action_points
    self._SubtractActionPoints(position)
    position.me.stance += 1
    return ap

  def _Undo(self, position, info):
    position.me.stance -= 1
    position.action_points = info

  def SetMove(self, position, move):
    move.action = ActionType.RAISE_STANCE


class LowerStance(Action):
  def _IsPossible(self, position):
    return position.me.stance != TrooperStance.PRONE

  def _ActionCost(self, position):
    return self.context.game.stance_change_cost

  def _Apply(self, position):
    ap = position.action_points
    self._SubtractActionPoints(position)
    position.me.stance -= 1
    return ap

  def _Undo(self, position, info):
    position.me.stance += 1
    position.action_points = info

  def SetMove(self, position, move):
    move.action = ActionType.LOWER_STANCE
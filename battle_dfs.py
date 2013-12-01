from actions import *
from constants import ALL_DIRS, PointAndDir
import dfs


class BattleSearcher(dfs.Searcher):

  def _TryMoves(self, walked_to):
    restr = self._constraints[-1]
    old_energizer = restr.can_energize
    old_can_heal = None
    old_shoot_at = None
    old_grenade = None
    old_shoot_at = old_shoot_at or set(zz for zz in restr.shoot_at)

    if self.pos.me.type == TrooperType.FIELD_MEDIC:
      old_can_heal = list(restr.can_heal)
      for ally in self.context.allies.itervalues():
        if restr.can_heal[ally.type]:
          self._Try(UseMedikit(self.context, ally.type), walked_to)
          restr.can_heal[ally.type] = False
          act = FieldMedicHeal(self.context, ally.type)
          extra = []
          while True:
            if not self._Try(act, walked_to, extra=extra):
              break
            extra += [act]


    if restr.can_energize and self.pos.holding_field_ration:
      # TODO: Force next move to be throwing grenade.
      if ((self.pos.holding_grenade and self.pos.action_points < self.pos.me.initial_action_points) or
          (self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points)):
        act = Energizer(self.context)
        if act.Allowed(self.pos):
          self._constraints.append(dfs.Constraints())
          # Energizer drops all constraints
          self._Try(act, walked_to)
          del self._constraints[-1]
        if self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points:
          restr.can_energize = False

    for xy in self.context.enemies:
      if xy not in restr.shoot_at:
        extra = []
        restr.shoot_at.add(xy)
        act = Shoot(self.context, xy)
        while True:
          if not self._Try(act, walked_to, extra=extra):
            break
          extra += [act]

    if self.pos.holding_grenade and self.pos.action_points >= self.context.game.grenade_throw_cost:
      old_grenade = set(zz for zz in restr.grenade_at)
      for xy in self.context.enemies:
        if xy in restr.grenade_at:
          continue
        act = ThrowGrenade(self.context, xy)
        if self._Try(act, walked_to):
          restr.grenade_at.add(xy)

        for d in ALL_DIRS:
          p1 = PointAndDir(xy, d)
          if p1 in restr.grenade_at:
            continue
          act = ThrowGrenade(self.context, p1)
          if self._Try(act, walked_to):
            restr.grenade_at.add(p1)

    for d in ALL_DIRS:
      p1 = PointAndDir(self.pos.me.xy, d)
      self._Try(Walk(self.context, p1), walked_to)

    restr.shoot_at = set()
    self._Try(RaiseStance(self.context), walked_to)
    self._Try(LowerStance(self.context), walked_to)

    restr.can_energize = old_energizer
    restr.shoot_at = old_shoot_at
    if old_can_heal is not None:
      restr.can_heal = old_can_heal
    if old_grenade is not None:
      restr.grenade_at = old_grenade


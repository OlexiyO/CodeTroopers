from actions import *
from constants import ALL_DIRS, PointAndDir
import dfs


class BattleSearcher(dfs.Searcher):

  def _TryMoves(self):
    restr = self._constraints[-1]
    old_energizer = restr.can_energize
    old_can_heal = None

    if self.pos.me.type == TrooperType.FIELD_MEDIC:
      old_can_heal = list(restr.can_heal)
      for ally in self.context.allies.itervalues():
        if restr.can_heal[ally.type]:
          if self._Try(FieldMedicHeal(self.context, ally.type)):
            restr.can_heal[ally.type] = False
          self._Try(UseMedikit(self.context, ally.type))

    if restr.can_energize and self.pos.holding_field_ration:
      # TODO: Force next move to be throwing grenade.
      if ((self.pos.holding_grenade and self.pos.action_points < self.pos.me.initial_action_points) or
          (self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points)):
        act = Energizer(self.context)
        if act.Allowed(self.pos):
          self._constraints.append(dfs.Constraints())
          # Energizer drops all constraints
          self._Try(act)
          del self._constraints[-1]
        if self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points:
          restr.can_energize = False

    old_grenade = None

    if self.pos.holding_grenade and self.pos.action_points >= self.context.game.grenade_throw_cost:
      old_grenade = set(zz for zz in restr.grenade_at)
      for xy in self.context.enemies:
        if xy in restr.grenade_at:
          continue
        act = ThrowGrenade(self.context, xy)
        if self._Try(act):
          restr.grenade_at.add(xy)

        for d in ALL_DIRS:
          p1 = PointAndDir(xy, d)
          if p1 in restr.grenade_at:
            continue
          act = ThrowGrenade(self.context, p1)
          if self._Try(act):
            restr.grenade_at.add(p1)

    self._Try(RaiseStance(self.context))
    self._Try(LowerStance(self.context))

    for xy in self.context.enemies:
      self._Try(Shoot(self.context, xy))

    for d in ALL_DIRS:
      p1 = PointAndDir(self.pos.me.xy, d)
      self._Try(Walk(self.context, p1))

    restr.can_energize = old_energizer
    if old_can_heal is not None:
      restr.can_heal = old_can_heal
    if old_grenade is not None:
      restr.grenade_at = old_grenade

from actions import *
from constants import ALL_DIRS, PointAndDir
import dfs


class BattleSearcher(dfs.Searcher):

  def _TryMoves(self):
    restr = self._constraints[-1]
    old_energizer = restr.can_energize
    old_can_heal = None
    if restr.can_energize:
      act = Energizer(self.context)
      if act.Allowed(self.pos):
        self._constraints.append(dfs.Constraints())
        # Energizer drops all constraints.
        self._Try(act)
        del self._constraints[-1]
      if (self.pos.holding_field_ration and
          self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points):
        restr.can_energize = False

    if self.pos.me.type == TrooperType.FIELD_MEDIC:
      old_can_heal = list(restr.can_heal)
      for ally in self.context.allies.itervalues():
        if restr.can_heal[ally.type]:
          if self._Try(FieldMedicHeal(self.context, ally.type)):
            restr.can_heal[ally.type] = False
          self._Try(UseMedikit(self.context, ally.type))

    if self.pos.holding_grenade and self.pos.action_points >= self.context.game.grenade_throw_cost:
      counts = {}
      for xy in self.context.enemies:
        for d in ALL_DIRS:
          p1 = PointAndDir(xy, d)
          counts[p1] = counts.get(p1, 0) + 1

      for xy in self.context.enemies:
        counts[xy] = 0

      for xy in self.context.enemies:
        too_far = self._Try(ThrowGrenade(self.context, xy))

        for d in ALL_DIRS:
          p1 = PointAndDir(xy, d)
          cc = counts[p1]
          if (too_far and cc > 0) or cc > 1:
            self._Try(ThrowGrenade(self.context, p1))

    self._Try(RaiseStance(self.context))
    self._Try(LowerStance(self.context))
    for d in ALL_DIRS:
      p1 = PointAndDir(self.pos.me.xy, d)
      self._Try(Walk(self.context, p1))

    # Why moving those lines at the bottom changes behavior?
    for xy in self.context.enemies:
      self._Try(Shoot(self.context, xy))

    restr.can_energize = old_energizer
    if old_can_heal is not None:
      restr.can_heal = old_can_heal

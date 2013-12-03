from actions import *
from constants import ALL_DIRS, PointAndDir
import dfs


class BattleSearcher(dfs.Searcher):

  def _TryMoves(self, can_walk):
    self._TryMedikit()
    self._TryGrenade()
    self._TryHeal()
    self._TryShoot()

    self._Try(RaiseStance(self.context), can_walk=True)
    self._Try(LowerStance(self.context), can_walk=False)
    if self.pos.holding_field_ration and self.pos.action_points < self.pos.me.initial_action_points:
      self._Try(Energizer(self.context), can_walk=True)
    if can_walk:
      self._TryWalk()

  def _TryShoot(self):
    for xy in self.context.enemies:
      self._Try(Shoot(self.context, xy), can_walk=True)

  def _TryGrenade(self):
    if not self.pos.holding_grenade or self.pos.action_points < self.context.game.grenade_throw_cost:
      return
    candidates = set(self.context.enemies.iterkeys())
    for xy in self.context.enemies:
      candidates.update(PointAndDir(xy, d) for d in ALL_DIRS)
    for xy in candidates:
      self._Try(ThrowGrenade(self.context, xy), can_walk=True)

  def _TryMedikit(self):
    if not self.pos.holding_medikit:
      return
    for ally_type, hp in enumerate(self.pos.allies_hp):
      ally = self.pos.GetUnit(ally_type)
      if ally is None:
        continue
      delta = ally.maximal_hitpoints - hp
      if delta > 0 and util.NextCell(self.pos.me.xy, ally.xy):
        self._Try(UseMedikit(self.context, ally.type), can_walk=True)

  def _TryHeal(self):
    if self.pos.me.type != TrooperType.FIELD_MEDIC:
      return
    for ally_type, hp in enumerate(self.pos.allies_hp):
      ally = self.pos.GetUnit(ally_type)
      if ally is None:
        continue
      delta = ally.maximal_hitpoints - hp
      if delta < 0 or not util.NextCell(self.pos.me.xy, ally.xy):
        continue
      hp_per_ap = (self.context.game.field_medic_heal_self_bonus_hitpoints
                   if ally_type == self.pos.me.type else
                   self.context.game.field_medic_heal_bonus_hitpoints)
      max_heal_count = min((delta + hp_per_ap - 1) / hp_per_ap, self.pos.action_points)
      if max_heal_count > 0:
        self._Try([FieldMedicHeal(self.context, ally.type)] * max_heal_count, can_walk=True)

  @util.TimeMe
  def _TryWalk(self):
    data = util.Array2D(0)
    Q = [self.pos.me.xy]
    LOA = [[]]
    pos = 0
    data[self.pos.me.xy.x][self.pos.me.xy.y] = self.pos.action_points
    move_cost = util.MoveCost(self.context, self.pos.me.stance)
    while pos < len(Q):
      p = Q[pos]
      A = LOA[pos]
      pos += 1
      points_left = data[p.x][p.y]
      if points_left < move_cost:
        continue
      points_left -= move_cost

      for d in ALL_DIRS:
        p1 = PointAndDir(p, d)
        if self.context.IsPassable(p1) and data[p1.x][p1.y] < points_left:
          data[p1.x][p1.y] = points_left
          if p1 not in self.context.allies and p1 not in self.context.enemies:
            bonus = self.context.bonuses.get(p1, None)
            actions = A + [Walk(self.context, p1)]
            can_walk_after = bonus is not None and not self.pos.HasBonus(bonus.type) and self.pos.bonuses_present[p1]
            self._Try(actions, can_walk=can_walk_after)
            Q.append(p1)
            LOA.append(A + [Walk(self.context, p1)])



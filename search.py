import actions
from actions import *
from evaluator import EvaluatePosition
import global_vars

M = []


class Constraints(object):
  def __init__(self):
    self.can_heal = True
    self.grenade_at = set()
    self.can_energize = True


class Searcher(object):
  @util.TimeMe
  def DoSearch(self, context):
    actions.context = context
    self.pos = Position(context)
    self.bestScore = EvaluatePosition(context, self.pos)
    self.bestAction = NoneAction(context)
    self.context = context
    self.fa = None
    self.total_count = 0
    self._constraints = [Constraints()]
    self._DFS(0)
    M.append((self.total_count, global_vars.TURN_INDEX))
    return self.bestAction

  def _Try(self, index, act):
    if not act.Allowed(self.pos):
      return False
    info = act.Apply(self.pos)
    if index == 0:
      self.fa = act
    self._DFS(index + 1)
    if index == 0:
      self.fa = None
    act.Undo(self.pos, info)
    return True

  def _DFS(self, index):
    self.total_count += 1
    if index > 0:
      score = EvaluatePosition(self.context, self.pos)
      if score > self.bestScore:
        self.bestScore, self.bestAction = score, self.fa


    restr = self._constraints[-1]
    reset_energizer = False
    if restr.can_energize:
      act = Energizer(self.context)
      if act.Allowed(self.pos):
        self._constraints.append(Constraints())
        # Energizer drops all constraints.
        self._Try(index, Energizer(self.context))
        del self._constraints[-1]
      if (self.pos.holding_field_ration and
          self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.context.me.initial_action_points):
        reset_energizer = True
        restr.can_energize = False

    reset_heal = False
    old_grenade = None
    if restr.can_heal:
      reset_heal = True
      restr.can_heal = False
      self._Try(index, Medikit(self.context, self.pos.loc))
    for xy in self.context.enemies:
      self._Try(index, Shoot(self.context, xy))

    if self.pos.holding_grenade and self.pos.action_points >= self.context.game.grenade_throw_cost:
      old_grenade = set(zz for zz in restr.grenade_at)
      for xy in self.context.enemies:
        if xy in restr.grenade_at:
          continue
        act = ThrowGrenade(self.context, xy)
        if act.Allowed(self.pos):
          self._Try(index, act)
          restr.grenade_at.add(xy)

        for d in ALL_DIRS:
          p1 = PointAndDir(xy, d)
          if p1 in restr.grenade_at:
            continue
          act = ThrowGrenade(self.context, p1)
          if act.Allowed(self.pos):
            self._Try(index, act)
            restr.grenade_at.add(p1)

    for d in ALL_DIRS:
      p1 = PointAndDir(self.pos.loc, d)
      self._Try(index, Walk(self.context, p1))
      if p1 in self.pos.allies_hp:
        self._Try(index, Medikit(self.context, p1))

    restr.can_heal = reset_heal
    restr.can_energize = reset_energizer
    if old_grenade is not None:
      restr.grenade_at = old_grenade
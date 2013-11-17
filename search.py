import actions
from actions import *
from evaluator import EvaluatePosition
import global_vars

M = []


class Searcher(object):
  def DoSearch(self, context):
    actions.context = context
    self.q = [(Position(context), None)]
    self.bestScore = EvaluatePosition(context, self.q[0][0])
    self.bestAction = NoneAction(context)
    self._Search(context)
    return self.bestAction

  @util.TimeMe
  def _Try(self, act):
    if not act.Allowed(self.pos):
      return False
    new_pos = act.Apply(self.pos)
    assert new_pos is not None
    self.q.append((new_pos, self.fa_to_save or act))
    return True

  @util.TimeMe
  def _Search(self, context):
    grenade_at = set()
    shot_at = set()
    index = 0
    # TODO: Use energizer at the first available option?
    # TODO: Use heal at the first available option?
    while index < len(self.q):
      self.pos, first_action = self.q[index]     # Must be updated between iterations
      if index > 0:
        score = EvaluatePosition(context, self.pos)
        if score > self.bestScore:
          self.bestScore, self.bestAction = score, first_action

      self.fa_to_save = first_action if index > 0 else None # Must be updated between iterations

      self._Try(MedikitYourself(context))
      self._Try(Energizer(context))
      for d in ALL_DIRS:
        self._Try(Walk(context, PointAndDir(self.pos.loc, d)))
      for xy in context.enemies:
        self._Try(Shoot(context, xy))

      grenade_locations = set()
      for xy in context.enemies:
        grenade_locations.add(xy)
        for d in ALL_DIRS:
          grenade_locations.add(PointAndDir(xy, d))
      for p in grenade_locations:
        if p in grenade_at:
          continue
        # TODO: Add options to eat energizer and immediately throw grenade after it.
        if self._Try(ThrowGrenade(context, p)):
          grenade_at.add(p)

      index += 1
    M.append((index, global_vars.TURN_INDEX))
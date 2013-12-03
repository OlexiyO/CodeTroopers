from actions import *
import battle_simulator
from constants import PointAndDir, ALL_DIRS
import global_vars
import util

CALLS = {}
M = []

# Grenade > Shoot > Heal
# Stance > Grenade > Heal
NEXT_BANNED_MOVES = {
  LowerStance: (RaiseStance, Walk, ThrowGrenade, FieldMedicHeal, UseMedikit),
  RaiseStance: (LowerStance, ThrowGrenade, FieldMedicHeal, UseMedikit),
  Walk: (RaiseStance, ),
  ThrowGrenade: (Shoot, UseMedikit, FieldMedicHeal),
  Shoot: (UseMedikit, FieldMedicHeal),
  FieldMedicHeal: (),
  UseMedikit: (),
  Energizer: (),
}

class Searcher(object):
  @util.TimeMe
  def DoSearch(self, evaluate_fn, context, move):
    self.evaluate_fn = evaluate_fn
    self.pos = Position(context)
    old_me, context.me = context.me, None
    battle_simulator.Precompute(context, self.pos)
    # Eval position as it was end of turn.
    ap = self.pos.action_points
    self.pos.action_points = 0
    self.bestScore = self.evaluate_fn(context, self.pos)
    self.pos.action_points = ap
    self.bestActions = [NoneAction(context)]
    self.context = context
    self.total_count = 0
    self.moves = [None] * 25
    self.index = 0
    self._DFS(can_walk=True)
    M.append((self.total_count, global_vars.TURN_INDEX))
    context.me = old_me
    best_act = self.bestActions[0]
    best_act.SetMove(self.pos, move)
    print 'Plan:', self.bestActions
    if isinstance(best_act, (UseMedikit, FieldMedicHeal, LowerStance, Energizer)):
      global_vars.FORCED_ACTIONS, global_vars.MOVE_INDEX = self.bestActions[1:], self.context.world.move_index
    else:
      global_vars.FORCED_ACTIONS, global_vars.MOVE_INDEX = [], None
    return self.bestActions

  def PrevMove(self):
    return self.moves[self.index - 1] if self.index > 0 else None

  def _Try(self, actions, can_walk):
    actions = actions if isinstance(actions, list) else [actions]
    assert isinstance(actions[0], BaseAction)
    banned_moves = NEXT_BANNED_MOVES.get(type(self.PrevMove()), ())
    a0 = actions[0]
    if isinstance(a0, banned_moves):
      return False

    to_undo = []
    success = True

    for act in actions:
      if not act.Allowed(self.pos):
        success = False
        break
      to_undo.append((act, act.Apply(self.pos)))
      self.moves[self.index] = act
      self.index += 1
      global CALLS
      CALLS[type(act)] = CALLS.get(type(act), 0) + 1
      if not success:
        break

    if success:
      self._DFS(can_walk=can_walk)

    for act, info in reversed(to_undo):
      self.index -= 1
      act.Undo(self.pos, info)
    return success

  def _DFS(self, can_walk):
    self.total_count += 1
    if self.index > 0:
      score = self.evaluate_fn(self.context, self.pos)
      if score > self.bestScore:
        self.bestScore, self.bestActions = score, list(self.moves[:self.index])
        #self.evaluate_fn(self.context, self.pos) # For debug

    if self.pos.action_points > 0:
      self._TryMoves(can_walk=can_walk)

  def _TryMoves(self, can_walk):
    raise NotImplementedError

  def _TryMedikit(self):
    if not self.pos.holding_medikit:
      return
    for ally_type, hp in enumerate(self.pos.allies_hp):
      ally = self.pos.GetUnit(ally_type)
      if ally is None:
        continue
      delta = ally.maximal_hitpoints - hp
      if delta > 0 and (util.NextCell(self.pos.me.xy, ally.xy) or ally_type == self.pos.me.type):
        self._Try(UseMedikit(self.context, ally.type), can_walk=True)

  def _TryHeal(self):
    if self.pos.me.type != TrooperType.FIELD_MEDIC:
      return
    for ally_type, hp in enumerate(self.pos.allies_hp):
      ally = self.pos.GetUnit(ally_type)
      if ally is None:
        continue
      delta = ally.maximal_hitpoints - hp
      if delta < 0:
        continue
      if util.NextCell(self.pos.me.xy, ally.xy) or ally_type == self.pos.me.type:
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


def PrintDict(prefix, format, d):
  print prefix + ':', ', '.join(format % tup for tup in sorted(d.iteritems(), key=lambda x: x[1], reverse=True))


def PrintDebugInfo():
  PrintDict('Func times', '%s: %.2f', util.TOTAL_TIME)
  print '\n'.join('Move %d: %d' % (t[1], t[0]) for t in sorted(M, reverse=True))
  print 'Total dfs leaves:', sum(x[0] for x in M)
  PrintDict('Time per move:', '%d: %.1f', util.MOVE_TIMES)
  PrintDict('Calls', '%s: %d', CALLS)


class BattleSearcher(Searcher):

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


class ScoutingSearcher(Searcher):

  def _TryMoves(self, can_walk):
    self._TryMedikit()
    self._TryHeal()
    self._Try(RaiseStance(self.context), can_walk=True)
    if can_walk:
      self._TryWalk()
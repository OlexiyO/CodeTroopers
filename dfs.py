import itertools
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
  Shoot: (UseMedikit, FieldMedicHeal, Shoot),
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
    self.to_undo = [None] * 25
    self.index = 0
    self._DFS(can_walk=True)
    M.append((self.total_count, global_vars.TURN_INDEX))
    context.me = old_me
    best_act = self.bestActions[0]
    best_act.SetMove(self.pos, move)
    print 'Goal:', global_vars.NextGoal(), ' Plan:', self.bestActions
    global_vars.FORCED_ACTIONS = []
    global_vars.FORCED_MOVE_ID = context.world.move_index, self.pos.me.type
    for n, act in enumerate(self.bestActions):
      if n > 0:
        if isinstance(self.bestActions[n - 1], (UseMedikit, FieldMedicHeal, LowerStance, Energizer, ThrowGrenade, Shoot)):
          global_vars.FORCED_ACTIONS.append(act)
        else:
          break
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

    success = True

    applied = 0
    for act in actions:
      if not act.Allowed(self.pos):
        success = False
        break
      self.moves[self.index] = act
      self.to_undo[self.index] = act.Apply(self.pos)
      self.index += 1
      applied += 1
      global CALLS
      CALLS[type(act)] = CALLS.get(type(act), 0) + 1
      if not success:
        break

    if success:
      self._DFS(can_walk=can_walk)

    for n in range(applied):
      self.index -= 1
      self.moves[self.index].Undo(self.pos, self.to_undo[self.index])
    return success

  def _DFS(self, can_walk):
    self.total_count += 1
    if self.index > 0:
      score = self.evaluate_fn(self.context, self.pos)
      if score > self.bestScore:
        self.bestScore, self.bestActions = score, list(self.moves[:self.index])

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
      if delta <= 0:
        continue
      if util.NextCell(self.pos.me.xy, ally.xy):
        self._Try(UseMedikit(self.context, ally.type), can_walk=True)
      elif ally_type == self.pos.me.type:
        self._Try(UseMedikit(self.context, ally.type), can_walk=True)

  def _TryHeal(self):
    if self.pos.me.type != TrooperType.FIELD_MEDIC:
      return
    for ally_type, hp in enumerate(self.pos.allies_hp):
      ally = self.pos.GetUnit(ally_type)
      if ally is None:
        continue
      delta = ally.maximal_hitpoints - hp
      if delta <= 0:
        continue
      time_to_heal = False
      if util.NextCell(self.pos.me.xy, ally.xy):
        time_to_heal = True
      elif ally_type == self.pos.me.type:
        time_to_heal = (self.index == 0 or isinstance(self.PrevMove(), Energizer))
      if time_to_heal:
        hp_per_ap = (self.context.game.field_medic_heal_self_bonus_hitpoints
                     if ally_type == self.pos.me.type else
                     self.context.game.field_medic_heal_bonus_hitpoints)
        max_heal_count = min((delta + hp_per_ap - 1) / hp_per_ap, self.pos.action_points)
        if max_heal_count > 0:
          self._Try([FieldMedicHeal(self.context, ally.type)] * max_heal_count, can_walk=True)

  @util.TimeMe
  def _TryWalk(self):
    data = util.Array2D(-1)
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
    self._TryEnergizer()
    if can_walk:
      self._TryWalk()

  def _TryEnergizer(self):
    if not self.pos.holding_field_ration or self.pos.action_points >= self.pos.me.initial_action_points:
      return
    if self.index > 0:
      prev_move = self.PrevMove()
      if not isinstance(prev_move, (Energizer, Walk)):
        data = self.to_undo[self.index - 1]
        prev_ap = data[0] if isinstance(data, tuple) else data
        # Could have used energizer last turn
        if prev_ap + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points:
          return

    # Apply only if we'll get full benefit.
    if self.pos.action_points + self.context.game.field_ration_bonus_action_points <= self.pos.me.initial_action_points:
      self._Try(Energizer(self.context), can_walk=True)
    elif self.pos.holding_grenade and self.pos.action_points < self.pos.me.initial_action_points:
      # Next step must be grenade.
      self._Try(Energizer(self.context), can_walk=False)

  def _TryShoot(self):
    options = [xy for xy in self.context.enemies if Shoot(self.context, xy).Allowed(self.pos)]
    if self.index > 0 and isinstance(self.PrevMove(), RaiseStance):
      self.pos.me.stance -= 1
      # Filter out whoever we could shot on the last turn.
      options = [xy for xy in options if not Shoot(self.context, xy).Allowed(self.pos)]
      self.pos.me.stance += 1
    options = sorted(options)
    num_shots = self.pos.action_points / self.pos.me.shoot_cost
    if not options or num_shots == 0:
      return
    for n in range(1, num_shots + 1):
      for actions in itertools.combinations_with_replacement(options, n):
        self._Try([Shoot(self.context, xy) for xy in actions], can_walk=True)

  def _TryGrenade(self):
    if not self.pos.holding_grenade or self.pos.action_points < self.context.game.grenade_throw_cost:
      return
    candidates = set(self.context.enemies.iterkeys())
    for xy in self.context.enemies:
      for d in ALL_DIRS:
        p1 = PointAndDir(xy, d)
        if self.context.IsInside(p1):
          candidates.add(p1)
    for xy in candidates:
      self._Try(ThrowGrenade(self.context, xy), can_walk=True)


class ScoutingSearcher(Searcher):

  def _TryMoves(self, can_walk):
    self._TryMedikit()
    self._TryHeal()
    self._Try(RaiseStance(self.context), can_walk=True)
    self._Try(RaiseStance(self.context), can_walk=True)
    self._Try(LowerStance(self.context), can_walk=True)

    if can_walk:
      self._TryWalk()
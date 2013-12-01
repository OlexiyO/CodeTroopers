from actions import *
import global_vars
import util

CALLS = {}
M = []

# Grenade > Shoot > Heal
# Stance > Grenade > Heal

NEXT_BANNED_MOVES = {
  LowerStance: (RaiseStance, Walk, ThrowGrenade, FieldMedicHeal, UseMedikit),
  RaiseStance: (LowerStance, ThrowGrenade, FieldMedicHeal, UseMedikit),
  Walk: (RaiseStance,),
  Shoot: (UseMedikit, FieldMedicHeal),
  ThrowGrenade: (Shoot, UseMedikit, FieldMedicHeal),
  }


class Constraints(object):
  def __init__(self):
    self.can_heal = [True] * TOTAL_UNIT_TYPES
    self.shoot_at = set()
    self.can_energize = True
    self.visited = set()
    self.grenade_at = set()
    self.can_shoot = True


class Searcher(object):
  @util.TimeMe
  def DoSearch(self, evaluate_fn, context, move):
    self.evaluate_fn = evaluate_fn
    self.pos = Position(context)
    old_me, context.me = context.me, None
    # Eval position as it was end of turn.
    ap = self.pos.action_points
    self.pos.action_points = 0
    self.bestScore = self.evaluate_fn(context, self.pos)
    self.pos.action_points = ap
    self.bestAction = NoneAction(context)
    self.context = context
    self.fa = None
    self.total_count = 0
    self._constraints = [Constraints()]
    self.last_move = [None] * 25
    self.index = 0
    self._DFS([])
    M.append((self.total_count, global_vars.TURN_INDEX))
    context.me = old_me
    self.bestAction.SetMove(self.pos, move)

  def LastMove(self):
    return self.last_move[self.index]

  def UpdateWhereTo(self, walked_to, act):
    if type(act) == Walk:
      if act.where in walked_to:
        return False, []
      else:
        return True, walked_to + [act.where]
    else:
      if isinstance(act, (FieldMedicHeal, UseMedikit)) and act.who == self.pos.me.type:
        return True, walked_to
      else:
        return True, []

  def _Try(self, A, walked_to, extra=None):
    actions = [A] + (extra or [])
    banned_moves = NEXT_BANNED_MOVES.get(type(self.LastMove()), ())
    act = actions[0]
    if isinstance(act, banned_moves):
      return False

    to_revert = []
    success = True
    where_moves = walked_to

    for act in actions:
      if not act.Allowed(self.pos):
        success = False
        break
      to_revert.append(act.Apply(self.pos))
      if self.index == 0:
        self.fa = act
      self.last_move[self.index + 1] = act
      self.index += 1
      global CALLS
      CALLS[type(act)] = CALLS.get(type(act), 0) + 1
      success, where_moves = self.UpdateWhereTo(where_moves, act)
      if not success:
        break

    if success:
      self._DFS(where_moves)

    for info in reversed(to_revert):
      self.index -= 1
      if self.index == 0:
        self.fa = None
      act.Undo(self.pos, info)
    return success

  def _DFS(self, walked_to):
    self.total_count += 1
    if self.index > 0:
      score = self.evaluate_fn(self.context, self.pos)
      if score > self.bestScore:
        self.bestScore, self.bestAction = score, self.fa

    if self.pos.action_points > 0:
      self._TryMoves(walked_to)

  def _TryMoves(self, walked_to):
    raise NotImplementedError


def PrintDict(prefix, format, d):
  print prefix + ':', ', '.join(format % tup for tup in sorted(d.iteritems(), key=lambda x: x[1], reverse=True))


def PrintDebugInfo():
  PrintDict('Func times', '%s: %.2f', util.TOTAL_TIME)
  print '\n'.join('Move %d: %d' % (t[1], t[0]) for t in sorted(M, reverse=True))
  print 'Total dfs leaves:', sum(x[0] for x in M)
  PrintDict('Time per move:', '%d: %.1f', util.MOVE_TIMES)
  PrintDict('Calls', '%s: %d', CALLS)

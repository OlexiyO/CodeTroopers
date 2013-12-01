from actions import *
import global_vars
import util

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
    self._DFS()
    M.append((self.total_count, global_vars.TURN_INDEX))
    context.me = old_me
    self.bestAction.SetMove(self.pos, move)

  def LastMove(self):
    return self.last_move[self.index]

  def _Try(self, act):
    banned_moves = NEXT_BANNED_MOVES.get(type(self.LastMove()), ())
    if isinstance(act, banned_moves):
      return False

    if not act.Allowed(self.pos):
      return False

    info = act.Apply(self.pos)
    if self.index == 0:
      self.fa = act
    self.last_move[self.index + 1] = act
    self.index += 1
    self._DFS()
    self.index -= 1
    if self.index == 0:
      self.fa = None
    act.Undo(self.pos, info)
    return True

  def _DFS(self):
    self.total_count += 1
    if self.index > 0:
      score = self.evaluate_fn(self.context, self.pos)
      if score > self.bestScore:
        self.bestScore, self.bestAction = score, self.fa

    if self.pos.action_points > 0:
      self._TryMoves()

  def _TryMoves(self):
    raise NotImplementedError


def PrintDebugInfo():
  print '\n'.join('%s: %.2f' % t for t in sorted(util.TOTAL_TIME.iteritems(), reverse=True, key=lambda x: x[1]))
  print '\n'.join('Move %d: %d' % (t[1], t[0]) for t in sorted(M, reverse=True))
  print 'Total dfs leaves:', sum(x[0] for x in M)
  print 'Time per move:', ', '.join('%d: %.1f' % tup for tup in sorted(util.MOVE_TIMES.iteritems(), key=lambda x: -x[1]))

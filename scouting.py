from actions import Position, FieldMedicHeal, UseMedikit
from constants import *
from dfs import ScoutingSearcher
import global_vars
import map_util
from model.ActionType import ActionType
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
import scouting_evaluator
import util


def _FindMostMissingHP(position, context):
  most_missing, where = 0, None
  for xy, ally in context.allies.iteritems():
    will_heal = min(
      ally.maximal_hitpoints - ally.hitpoints,
      context.game.medikit_heal_self_bonus_hitpoints if xy == position.me.xy else context.game.medikit_bonus_hitpoints)
    if will_heal > most_missing:
      most_missing, where = will_heal, xy
  return most_missing, where


def MaybeMedikit(position, context, move):
  if not position.me.holding_medikit:
    return False
  most_missing, where = _FindMostMissingHP(position, context)
  if most_missing <= 0:
    return False
  who = context.allies[where].type
  if util.NextCell(where, position.me.xy) or where == position.me.xy:
    act = UseMedikit(context, who)
    if act.Allowed(position):
      act.SetMove(position, move)
      return True
    else:
      return False
  else:
    return RunTo(where, context, move)


def MaybeHeal(position, context, move):
  for d in ALL_DIRS:
    where = PointAndDir(position.me.xy, d)
    if where in context.allies:
      who = context.allies[where].type
      act = FieldMedicHeal(context, who)
      if act.Allowed(position):
        act.SetMove(position, move)
        return True

  act = FieldMedicHeal(context, position.me.type)
  if act.Allowed(position):
    act.SetMove(position, move)
    return True

  most_missing, where = _FindMostMissingHP(position, context)
  if most_missing <= 0:
    return False
  who = context.allies[where].type
  if util.NextCell(where, position.me.xy) or where == position.me.xy:
    act = FieldMedicHeal(context, who)
    if act.Allowed(position):
      act.SetMove(position, move)
    else:
      act.action = ActionType.END_TURN
    return True
  else:
    return RunTo(where, context, move)


def TryHeal(context, move):
  # TODO: Better heal between moves.
  position = Position(context)
  me = position.me
  if any(ally.type == TrooperType.FIELD_MEDIC for ally in context.allies.itervalues()):
    if me.type == TrooperType.FIELD_MEDIC:
      return MaybeHeal(position, context, move)
    else:
      if me.maximal_hitpoints > me.hitpoints:
        for p, ally in context.allies.iteritems():
          if ally.type == TrooperType.FIELD_MEDIC:
            return RunTo(p, context, move)
      else:
        return False
  else:
    if MaybeMedikit(position, context, move):
      return True

  return False


def StanceForRunning(context, trooper):
  #if context.MapIsOpen() and trooper.type == TrooperType.SNIPER:
  #  return TrooperStance.KNEELING
  #else:
  return TrooperStance.STANDING


@util.TimeMe
def ScoutingMove(context, move):
  # Leave 2 steps.
  global_vars.CheckIfAchievedGoal(context.me.xy)
  #if global_vars.LAST_SEEN_ENEMIES < context.world.move_index - 5:
  if context.me.action_points >= 2:
    if context.me.stance < StanceForRunning(context, context.me):
      move.action = ActionType.RAISE_STANCE
      return
    elif context.me.stance > StanceForRunning(context, context.me):
      move.action = ActionType.LOWER_STANCE
      return

  searcher = ScoutingSearcher()
  return searcher.DoSearch(scouting_evaluator.EvaluatePosition, context, move)


def SetWalk(where, move):
  move.action = ActionType.MOVE
  move.x, move.y = where.x, where.y


@util.TimeMe
def RunTo(where, context, move):
  """Tells unit to run to 'where'."""
  assert where != context.me.xy
  me = context.me
  best_d = context.steps[where.x][where.y]

  if context.me.stance < StanceForRunning(context, context.me):
    move.action = ActionType.RAISE_STANCE
    return True
  elif context.me.stance > StanceForRunning(context, context.me):
    move.action = ActionType.LOWER_STANCE
    return True

  options = []
  if best_d < 100:
    data = context.FindDistances(where)
    curr = best_d
    for d in ALL_DIRS:
      p1 = PointAndDir(context.me.xy, d)
      if context.CanMoveTo(p1) and data[p1.x][p1.y] == curr - 1:
        options.append(p1)
  else:
    dmap = global_vars.distances[where.x][where.y]
    now = dmap[context.me.x][context.me.y]
    for d in ALL_DIRS:
      p1 = PointAndDir(context.me.xy, d)
      if context.CanMoveTo(p1) and dmap[p1.x][p1.y] == now - 1:
        options.append(p1)

  if not options:
    return False

  with_dist = sorted([(context.DistFromHerd(me, xy), xy) for xy in options])
  if with_dist[0][0] <= max(context.CloseEnough(), context.DistFromHerd(me, context.me.xy)):
    SetWalk(with_dist[0][1], move)
    return True

  return False

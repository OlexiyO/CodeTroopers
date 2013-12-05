from constants import *
from dfs import ScoutingSearcher
import global_vars
from model.ActionType import ActionType
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
import scouting_evaluator
import util


def StanceForRunning(context, trooper):
  #if context.MapIsOpen() and trooper.type == TrooperType.SNIPER:
  #  return TrooperStance.KNEELING
  #else:
  return TrooperStance.STANDING


@util.TimeMe
def ScoutingMove(context, move):
  # Leave 2 steps.
  DELAY = 5  # How many turns to wait before sending an airplane.
  if context.me.type == TrooperType.COMMANDER:
    my_index = context.me.player_id
    positions = [util.ClosestEmptyCell(context, Point(player.approximate_x, player.approximate_y)) for player in context.world.players
                 if player.approximate_x != -1 and player.approximate_y != -1 and player.id != my_index]
    with_dist = sorted((util.ManhDist(p, context.me.xy), p) for p in positions)
    if with_dist:
      next_goal = with_dist[0][1]
      global_vars.UpdateSeenEnemies(context, [util.ClosestEmptyCell(context, next_goal)])
  if (global_vars.LAST_SEEN_ENEMIES < context.world.move_index - DELAY and
      context.me.type == TrooperType.COMMANDER and
      context.me.action_points >= context.game.commander_request_enemy_disposition_cost):
    move.action = ActionType.REQUEST_ENEMY_DISPOSITION
    return
  CheckIfAchievedGoal(context)
  #all_allies = [x for x in context.allies] + [context.me.xy]
  #max_d = max(max(util.ManhDist(a, b) for a in all_allies) for b in all_allies)
  #if max_d > params.
  if global_vars.LAST_SEEN_ENEMIES < context.world.move_index - DELAY and global_vars.LAST_SWITCHED_GOAL < context.world.move_index - 8:
    global_vars.SwitchToNextGoal(context.world.move_index)

  if context.me.action_points >= 2:
    if context.me.stance < StanceForRunning(context, context.me):
      move.action = ActionType.RAISE_STANCE
      return
    elif context.me.stance > StanceForRunning(context, context.me):
      move.action = ActionType.LOWER_STANCE
      return

  searcher = ScoutingSearcher()
  return searcher.DoSearch(scouting_evaluator.EvaluatePosition, context, move)


def CheckIfAchievedGoal(context):
  g = global_vars.NextGoal()
  xy = context.me.xy
  if util.IsVisible(context, 4, xy.x, xy.y, TrooperStance.PRONE, g.x, g.y, TrooperStance.PRONE):
    global_vars.SwitchToNextGoal(context.world.move_index)

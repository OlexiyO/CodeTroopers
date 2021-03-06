import os
import cPickle as pickle
from MyStrategy import MyStrategy
import global_vars
import map_util
import util

TEST_DIR = 'C:/Coding/CodeTroopers/src/tests/testdata'

def ContextFromFile(filename):
  with open(os.path.join(TEST_DIR, '%s.pickle' % filename)) as fin:
    context = pickle.load(fin)
  map_name = filename[filename.rfind('_') + 1:]
  with open(os.path.join(TEST_DIR, 'visibilities_%s' % map_name)) as fin:
    context.world.cell_visibilities = pickle.load(fin)
  context.world.stance_count = 3
  s = MyStrategy()
  s.Init(context)
  global_vars.UNITS_IN_GAME = context.TOTAL_UNITS
  global_vars.UNITS_ORDER = context.UNITS_ORDER
  global_vars.NEXT_CORNER = context.NEXT_CORNER
  global_vars.ORDER_OF_CORNERS = context.ORDER_OF_CORNERS
  context.map_name = map_util.MapName(context)
  s.FillCornersOrder(context)
  global_vars.FORCED_ACTIONS = []
  global_vars.POSITION_AT_START_MOVE = context.me.xy

  print 'Enemies', [util.PrintTrooper(e) for e in context.enemies.itervalues()]
  print 'Allies', [util.PrintTrooper(a) for a in context.allies.itervalues()]
  print 'Me %s with %d ap' % (util.PrintTrooper(context.me), context.me.action_points)

  return s, context



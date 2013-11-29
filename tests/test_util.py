import os
import cPickle as pickle
from Strategy import Strategy
import global_vars

TEST_DIR = 'C:/Coding/CodeTroopers/src/tests/testdata'

def ContextFromFile(filename):
  with open(os.path.join(TEST_DIR, '%s.pickle' % filename)) as fin:
    context = pickle.load(fin)
  map_name = filename[filename.rfind('_') + 1:]
  with open(os.path.join(TEST_DIR, 'visibilities_%s' % map_name)) as fin:
    context.world.cell_visibilities = pickle.load(fin)
  context.world.stance_count = 3
  s = Strategy()
  s.Init(context)
  global_vars.UNITS_IN_GAME = context.TOTAL_UNITS
  global_vars.UNITS_ORDER = context.UNITS_ORDER
  global_vars.NEXT_CORNER = context.NEXT_CORNER
  global_vars.ORDER_OF_CORNERS = context.ORDER_OF_CORNERS
  context._FillVisibleCells()
  context._FillDistancesFromMe()

  return s, context



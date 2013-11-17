import os
from MyStrategy import MyStrategy
from model.Move import Move

D = 'C:/Coding/CodeTroopers/logs/1116_183045/'
path = os.path.join(D, '044_3_1.pickle')
cv_path = os.path.join(D, 'visibilities')

import cPickle as pickle

with open(path) as fin:
  context = pickle.load(fin)

with open(cv_path) as fin:
  context.world.cell_visibilities = pickle.load(fin)

MyStrategy().RealMove(context, Move())
import os
from MyStrategy import MyStrategy
from model.Move import Move

D = 'C:/Coding/CodeTroopers/logs/1120_223254'
path = os.path.join(D, '085_5_1.pickle')


import cPickle as pickle

with open(path) as fin:
  context = pickle.load(fin)

cv_path = os.path.join(D, 'visibilities')

with open(cv_path) as fin:
  context.world.cell_visibilities = pickle.load(fin)

MyStrategy().RealMove(context, Move())
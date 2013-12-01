from actions import *
from constants import ALL_DIRS, PointAndDir
import dfs


class ScoutingSearcher(dfs.Searcher):

  def _TryMoves(self, walked_to):
    for d in ALL_DIRS:
      p1 = PointAndDir(self.pos.me.xy, d)
      self._Try(Walk(self.context, p1), walked_to)

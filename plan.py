class Plan(object):
  def __init__(self, context):
    self.context = context
    self.profit = 0
    self.cost = 0
    self.risk = 0
    self.is_possible = False
    self.Compute()

  def SetNextStep(self, move):
    raise NotImplementedError

  def Compute(self):
    raise NotImplementedError


class MoveToGoal(Plan):
  def Compute(self):
     pass
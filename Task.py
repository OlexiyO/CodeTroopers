

class Task(object):
  def IsDone(self):
    raise NotImplementedError

  def CheckLimitations(self):
    raise NotImplementedError

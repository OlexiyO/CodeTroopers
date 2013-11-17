from subprocess import call
from threading import Thread


def T1():
  call('python Validation.py 31000', shell=True, cwd='C:/Coding/CodeTroopers/src')

def T2():
  call('python Validation.py 32000 map1', shell=True, cwd='C:/Coding/CodeTroopers/src')


#t1 = Thread(target=T1)
t2 = Thread(target=T2)
#t1.start()
t2.start()

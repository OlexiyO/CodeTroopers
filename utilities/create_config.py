import tempfile

CONFIG = """
render-to-screen=%(render)s
render-to-screen-sync=%(render)s
results-file=%(output_filepath)s
team-size=4
player-count=4
p1-type=Local
p2-type=Local
p3-type=Local
p4-type=Local

# List of maps: default, empty, cheeser, map01, map02, map03.
map=%(map_name)s

base-adapter-port=%(base_port)s
seed=%(seed)s
"""


def CreateConfigFile(**kwargs):
  my_player_index = kwargs.pop('my_player_index', None)
  if my_player_index is None:
    names = [''] * 4
  else:
    names = ['Latest' if my_player_index == n else 'Old' for n in range(4)]
  config_filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
  print config_filepath
  if 'seed' in kwargs and kwargs['seed'] == '0000000000000000':
    kwargs['seed'] = None
  with open(config_filepath, 'w') as fout:
    fout.write(CONFIG % kwargs)
    for n, name in zip([1, 2, 3, 4], names):
      fout.write('p%d-name=%s\n' % (n, name))

  return config_filepath
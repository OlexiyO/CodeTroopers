import hashlib

HEX_DIGESTS = {
  '3f96d08acaa3e9e119e3d2132350e2cb': 'map03',
  '0b939d75af93ae8e8c01b5d17faa7dd1': 'cheeser',
  'a0a6a9631a915a30e800f638d6a388b0': 'map02',
  }


def MapIsOpen(map_name):
  return map_name != 'cheeser'


def MapName(context):
  return HEX_DIGESTS.get(HashOfMap(context), '')


def HashOfMap(context):
  md = hashlib.md5()
  for row in context.world.cells:
    md.update(''.join('%d' % c for c in row))
  return md.hexdigest()


def SecureOnFirstTurn(context):
  map_name = context.map_name
  return map_name not in ['cheeser', 'map03', 'map02']


def RelaxAttackingOrder(context):
  map_name = context.map_name
  return map_name not in ['cheeser', 'map03']
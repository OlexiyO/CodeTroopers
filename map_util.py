import hashlib

HEX_DIGESTS = {
  'map03': '3f96d08acaa3e9e119e3d2132350e2cb',
  'cheeser': '0b939d75af93ae8e8c01b5d17faa7dd1',
  }
def HashOfMap(context):
  md = hashlib.md5()
  for row in context.world.cells:
    md.update(''.join('%d' % c for c in row))
  return md.hexdigest()
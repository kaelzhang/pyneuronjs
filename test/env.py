import os
__dirname = os.path.dirname(os.path.realpath(__file__))

def path_join(root, relative):
  return os.path.normpath(
    os.path.join(root, relative)
  )

ABSPATH = path_join(__dirname, '../')

import json
import sys
sys.path.append(ABSPATH)

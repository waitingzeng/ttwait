import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import os.path

extra_path = os.path.join(os.path.dirname(__file__), '3rdlib')
if extra_path not in sys.path:
    sys.path.insert(0, extra_path)

import os
import re
import sys
sys.path.append(os.getcwd())
sys.path.append("..")

from QtSLIX._cmd.main import main

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())

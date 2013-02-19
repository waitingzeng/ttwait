import os
os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"

from pycomm.ext_tornado.daemon_server import run_django_server as main


if __name__ == '__main__':
    main()    


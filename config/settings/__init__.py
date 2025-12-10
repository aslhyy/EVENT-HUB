from decouple import config

# Determine which settings to use based on DEBUG environment variable
DEBUG = config('DEBUG', default=True, cast=bool)

if DEBUG:
    from .dev import *
else:
    from .prod import *

import pymysql
pymysql.install_as_MySQLdb()
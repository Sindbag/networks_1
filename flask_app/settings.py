import os

SALT = os.getenv('NETWORK_SALT', '$0m3_4n07H39_KE8')

DATABASE = '/usr/src/some.db'
USERBASE = '/usr/src/users.db'

SECRET_KEY = '1234567890'
SESSION_TYPE = 'filesystem'

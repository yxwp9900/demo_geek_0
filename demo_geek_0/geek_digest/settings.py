import os

PROJECT_ENV = os.environ.get('PROJECT_ENV', 'test')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'geekpark-jwt')
JWT_EXPIRATION_DELTA = os.environ.get('JWT_EXPIRATION_DELTA', 6)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '27017'))
DB_NAME = os.environ.get('DB_NAME', 'geek_digest')

SKR_API_KEY = os.environ.get('SKR_API_KEY', '')

MIRROR_HOST = os.environ.get('MIRROR_HOST', 'http://data.geekpark.net')
SKR_HOST = os.environ.get('SKR_HOST', 'http://kong.geeks.vc')

CN_NEWS = f'{MIRROR_HOST}/api/v1/geeksread'
EN_NEWS = f'{SKR_HOST}/skr/cluster'

TRANSLATE_FROM = os.environ.get('TRANSLATE_FROM', 'sogou')

MD5_SALT = os.environ.get('MD5_SALT', '')

ICON_URL = 'https://holoread-img.geekpark.net/app/icon/{source}.png'

from .settings import * # pylint: disable=unused-wildcard-import, wildcard-import

ALLOWED_HOSTS = [
    'masproblemtest.strom.sk',
]

USE_X_FORWARDED_HOST = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

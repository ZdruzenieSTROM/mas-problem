from .settings import *  # pylint: disable=unused-wildcard-import, wildcard-import

# Lokálny vývoj: emaily sa neposielajú, ukladajú sa do súborov v priečinku emails/
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'emails'

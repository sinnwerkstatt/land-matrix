from .base import *  # noqa

DEBUG = True
SECRET_KEY = "MAGIC_CI_SECRET_KEY"

INTERNAL_IPS = ("127.0.0.1",)

# RECAPTCHA_USE_SSL = True
# NOCAPTCHA = True
# RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
# RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

TWITTER_TIMELINE = None


BROKER_URL = "redis://redis:6379/0"
CELERY_REDIS_BACKEND = BROKER_URL
CELERY_NAME = "landmatrix"

OLD_ELASTIC = True

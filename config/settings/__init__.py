"""
Import appropriate settings based on environment
"""
import os

ENV = os.getenv('DJANGO_ENV', 'development')

if ENV == 'production':
    from .production import *
elif ENV == 'development':
    from .development import *
else:
    from .base import *

"""
WSGI config for EduTrack Pro project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edutrack_pro.settings')

application = get_wsgi_application()

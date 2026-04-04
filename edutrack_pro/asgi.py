"""
ASGI config for EduTrack Pro project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edutrack_pro.settings')

application = get_asgi_application()

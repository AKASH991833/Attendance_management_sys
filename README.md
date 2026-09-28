# EduTrack Pro - Multi-Teacher Attendance Management System

A Django web application for schools and coaching classes: multiple teachers manage their own students, timetables and attendance, while a super admin oversees teachers, classes and reports.

## Features

- Teacher accounts with individual workspaces
- Student management per class
- Daily attendance marking and history
- Timetable management
- Calendar and holiday tracking
- Reports with export
- Notifications and WhatsApp broadcast
- Super admin dashboard for managing teachers and classes
- PWA support (installable on phones)

## Technology stack

- Django (Python), SQLite for development, MySQL for production
- HTML/CSS/JavaScript frontend with a glassmorphism theme

## Quick start

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperadmin   # creates the super admin account
python manage.py runserver          # http://127.0.0.1:8000/
```

Create each teacher account from the super admin panel before signing in at `/login/`. To use MySQL in production, update the database settings and see `MYSQL_SETUP.md`.

## Documentation

- `setup_instructions.md` - detailed setup
- `SUPER_ADMIN_GUIDE.md` - admin workflows
- `THEME_CUSTOMIZATION_GUIDE.md` - theming

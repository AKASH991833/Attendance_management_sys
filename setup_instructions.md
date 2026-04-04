# EduTrack Pro - Setup Instructions

## Smart Multi-Teacher Attendance & Communication System

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Database Setup](#database-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Production Deployment](#production-deployment)
7. [WhatsApp API Setup](#whatsapp-api-setup)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **MySQL 8.0 or higher** - [Download MySQL](https://dev.mysql.com/downloads/mysql/)
- **pip** (Python package manager) - Usually included with Python
- **Git** (optional, for version control) - [Download Git](https://git-scm.com/)

### Verify Installations

```bash
python --version    # Should show Python 3.10+
mysql --version     # Should show MySQL 8.0+
pip --version       # Should show pip version
```

---

## Installation

### Step 1: Navigate to Project Directory

```bash
cd C:\Users\akash\OneDrive\Desktop\Attendence\edutrack_pro
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Install MySQL Client (if needed)

**Windows:**
```bash
pip install mysqlclient
```
If you encounter errors, download pre-built wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3-devel mysql-devel gcc
pip install mysqlclient
```

---

## Database Setup

### Step 1: Create MySQL Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE edutrack_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'edutrack_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON edutrack_pro.* TO 'edutrack_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 2: Configure Environment Variables

Copy the example environment file:

```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac
```

Edit `.env` file with your settings:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=edutrack_pro
DB_USER=edutrack_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306

# WhatsApp Settings (Optional)
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### Step 3: Generate Secret Key (Optional)

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## Running the Application

### Step 1: Run Migrations

```bash
python manage.py migrate
```

### Step 2: Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 3: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 4: Create Media Directories

```bash
mkdir media\profile_pictures
mkdir media\workspace_files
```

### Step 5: Run Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

### Step 6: Access Admin Panel

Navigate to: **http://127.0.0.1:8000/admin/**

---

## Production Deployment

### Using Gunicorn and Nginx (Linux/Ubuntu)

#### Step 1: Install Gunicorn

```bash
pip install gunicorn
```

#### Step 2: Create Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 3
accesslog = "/var/log/edutrack/access.log"
errorlog = "/var/log/edutrack/error.log"
capture_output = True
enable_stdio_inheritance = True
```

#### Step 3: Create Systemd Service

Create `/etc/systemd/system/edutrack.service`:

```ini
[Unit]
Description=EduTrack Pro Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/edutrack_pro
ExecStart=/path/to/venv/bin/gunicorn --config gunicorn.conf.py edutrack_pro.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Step 4: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable edutrack
sudo systemctl start edutrack
sudo systemctl status edutrack
```

#### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/edutrack`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /path/to/edutrack_pro/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/edutrack_pro/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/edutrack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: Setup SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## WhatsApp API Setup

### Option 1: Twilio (Recommended for Development)

#### Step 1: Create Twilio Account

1. Sign up at [https://www.twilio.com/](https://www.twilio.com/)
2. Navigate to Console Dashboard

#### Step 2: Get Credentials

- **Account SID**: Found on Console Dashboard
- **Auth Token**: Found on Console Dashboard
- **WhatsApp Number**: Use Twilio's sandbox number `whatsapp:+14155238886`

#### Step 3: Configure Sandbox

1. Go to Messaging > Try it out > Send a WhatsApp message
2. Follow instructions to connect your WhatsApp number
3. Update `.env` file:

```env
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### Option 2: Meta Cloud API (Production)

#### Step 1: Create Meta Developer Account

1. Go to [https://developers.facebook.com/](https://developers.facebook.com/)
2. Create a new app

#### Step 2: Add WhatsApp Product

1. Add WhatsApp product to your app
2. Get Phone Number ID and Access Token

#### Step 3: Configure `.env`

```env
WHATSAPP_PROVIDER=meta
META_PHONE_NUMBER_ID=your_phone_number_id
META_WHATSAPP_TOKEN=your_access_token
```

#### Step 4: Verify Webhook (for incoming messages)

Set webhook URL to: `https://your-domain.com/api/whatsapp/webhook/`

---

## Troubleshooting

### Common Issues

#### 1. MySQL Connection Error

```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution:**
- Ensure MySQL service is running
- Check database credentials in `.env`
- Verify database exists

#### 2. Static Files Not Loading

```
404 Not Found - /static/css/main.css
```

**Solution:**
```bash
python manage.py collectstatic --noinput
```

#### 3. Permission Denied for Media Files

**Solution:**
```bash
# Linux
chmod -R 755 media/
chown -R www-data:www-data media/
```

#### 4. ModuleNotFoundError: mysqlclient

**Solution:**
```bash
# Install MySQL development headers
sudo apt-get install default-libmysqlclient-dev build-essential
pip install mysqlclient
```

#### 5. CSRF Token Error

**Solution:**
- Ensure `{% csrf_token %}` is in all POST forms
- Check CSRF_COOKIE_SECURE setting matches your deployment

### Debug Mode

For debugging, enable DEBUG in `.env`:

```env
DEBUG=True
```

Check logs at:
- Django console output
- `/var/log/edutrack/error.log` (production)

---

## Default Credentials

After running `createsuperuser`, use those credentials to login.

Default admin URL: `/admin/`
Default login URL: `/login/`

---

## Support

For issues and questions:
1. Check this documentation
2. Review Django logs for errors
3. Ensure all prerequisites are met

---

## Self-Validation Checklist

After setup, verify the following:

### Core Functionality
- [ ] Login/Logout works
- [ ] Registration creates new teacher
- [ ] Dashboard displays stats correctly
- [ ] Charts render with data

### Student Management
- [ ] Can add new student
- [ ] Can edit student details
- [ ] Can delete student
- [ ] Batch management works

### Attendance
- [ ] Can mark attendance for batch
- [ ] Attendance history shows records
- [ ] Student detail shows attendance percentage
- [ ] Holiday blocks attendance marking

### Timetable
- [ ] Weekly view displays correctly
- [ ] Can add/edit/delete slots
- [ ] Time conflict detection works

### Calendar
- [ ] Calendar renders with holidays
- [ ] Can add holiday/exam/event
- [ ] Can delete holidays

### Communications
- [ ] Broadcast form works
- [ ] Templates load correctly
- [ ] Messages send (or simulate)

### Workspace
- [ ] Notes CRUD operations work
- [ ] File upload works
- [ ] File download works
- [ ] File delete removes from disk

### Reports
- [ ] Batch attendance report generates
- [ ] Low attendance report shows correct students
- [ ] Excel export downloads
- [ ] PDF export downloads

### Notifications
- [ ] Notification badge updates
- [ ] Can mark as read
- [ ] Low attendance triggers notification

### PWA
- [ ] Service worker registers
- [ ] Install prompt appears
- [ ] Offline page loads when disconnected

### Security
- [ ] Teacher isolation enforced
- [ ] CSRF protection active
- [ ] Login required on all pages
- [ ] File upload validation works

---

**EduTrack Pro** - Built with Django | Version 1.0

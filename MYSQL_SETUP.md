# 🗄️ MySQL Database Setup Guide for EduTrack Pro

## Current Status
✅ **Application is working with SQLite** (development database)

## When to Use MySQL?
- Production deployment
- Multiple users accessing simultaneously
- Better performance for large datasets
- Backup and replication needs

---

## Option 1: Install MySQL on Windows

### Step 1: Download MySQL
1. Visit: https://dev.mysql.com/downloads/mysql/
2. Download "MySQL Installer for Windows"
3. Run the installer

### Step 2: Install MySQL
1. Choose "Developer Default" or "Server only"
2. Set root password (remember this!)
3. Complete the installation
4. Note: MySQL runs on port 3306 by default

### Step 3: Create Database
Open Command Prompt and run:
```bash
cd C:\Users\akash\OneDrive\Desktop\Attendence\edutrack_pro
mysql -u root -p < setup_mysql_database.sql
```
Enter your MySQL root password when prompted.

### Step 4: Update .env File
Edit `.env` file and add:
```env
DB_NAME=edutrack_pro
DB_USER=edutrack_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=3306
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Restart Server
Stop the current server (Ctrl+C) and restart:
```bash
python manage.py runserver
```

---

## Option 2: Use SQLite (Current Setup)

✅ **No MySQL installation needed!**

The application is currently running with SQLite which is:
- Perfect for development and testing
- Single file database (db.sqlite3)
- No additional software required
- Easy to backup (just copy the file)

### Limitations of SQLite:
- Not suitable for multiple concurrent users
- No network access
- Limited scalability

---

## Verify MySQL Connection

After setting up MySQL, test the connection:

```bash
# Test MySQL connection
mysql -u edutrack_user -p edutrack_pro
```

If successful, you'll see the MySQL prompt.

---

## Migration from SQLite to MySQL

If you want to migrate existing data:

### Step 1: Export SQLite data
```bash
python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes --indent 2 > data.json
```

### Step 2: Setup MySQL
Follow the MySQL setup steps above.

### Step 3: Import data
```bash
python manage.py loaddata data.json
```

---

## Production MySQL Configuration

For production deployment, update `.env`:

```env
# Production MySQL Settings
DB_NAME=edutrack_pro
DB_USER=edutrack_prod_user
DB_PASSWORD=very_secure_password_123!
DB_HOST=mysql-server-ip-or-hostname
DB_PORT=3306

# Security Settings
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SECRET_KEY=generate-new-secret-key-here
```

---

## Troubleshooting

### Error: "Access denied for user"
- Check username/password in `.env`
- Verify user has privileges: `SHOW GRANTS FOR 'edutrack_user'@'localhost';`

### Error: "Can't connect to MySQL server"
- Ensure MySQL service is running
- Check if port 3306 is open
- Verify DB_HOST is correct

### Error: "No module named 'MySQLdb'"
```bash
pip install mysqlclient
```

---

## Quick Reference

### Start MySQL Service (Windows)
```bash
net start MySQL80
```

### Stop MySQL Service (Windows)
```bash
net stop MySQL80
```

### Login to MySQL
```bash
mysql -u root -p
```

### Show Databases
```sql
SHOW DATABASES;
```

### Drop Database (if needed)
```sql
DROP DATABASE edutrack_pro;
```

---

**Current Setup:** ✅ SQLite (Development)  
**Ready for MySQL:** Yes, just update `.env` and run migrations!

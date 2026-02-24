#!/usr/bin/env python3
"""
OPENWORLD LOGIN DEBUG SCRIPT
Run this to identify and fix login issues
"""

import sys
import os

print("\n" + "="*70)
print("🔐 OPENWORLD LOGIN DEBUGGER")
print("="*70 + "\n")

issues_found = []
all_good = True

# ===== TEST 1: Check Python Version =====
print("1️⃣ Checking Python version...")
if sys.version_info >= (3, 6):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor} OK\n")
else:
    print(f"   ❌ Python 3.6+ required (you have {sys.version_info.major}.{sys.version_info.minor})\n")
    all_good = False
    issues_found.append("Python version too old")

# ===== TEST 2: Check Flask =====
print("2️⃣ Checking Flask...")
try:
    import flask
    print(f"   ✅ Flask {flask.__version__} installed\n")
except ImportError as e:
    print(f"   ❌ Flask not installed: {e}")
    print("   Fix: pip install Flask\n")
    all_good = False
    issues_found.append("Flask not installed")

# ===== TEST 3: Check Flask-Login =====
print("3️⃣ Checking Flask-Login...")
try:
    from flask_login import LoginManager, login_user, current_user
    print(f"   ✅ Flask-Login installed\n")
except ImportError as e:
    print(f"   ❌ Flask-Login not installed: {e}")
    print("   Fix: pip install Flask-Login --break-system-packages\n")
    all_good = False
    issues_found.append("Flask-Login not installed")

# ===== TEST 4: Check SQLAlchemy =====
print("4️⃣ Checking SQLAlchemy...")
try:
    import sqlalchemy
    print(f"   ✅ SQLAlchemy {sqlalchemy.__version__} installed\n")
except ImportError as e:
    print(f"   ❌ SQLAlchemy not installed: {e}")
    print("   Fix: pip install SQLAlchemy\n")
    all_good = False
    issues_found.append("SQLAlchemy not installed")

# ===== TEST 5: Check Werkzeug =====
print("5️⃣ Checking Werkzeug...")
try:
    from werkzeug.security import generate_password_hash, check_password_hash
    print(f"   ✅ Werkzeug installed\n")
    
    # Test password hashing
    test_hash = generate_password_hash("test123")
    test_check = check_password_hash(test_hash, "test123")
    if test_check:
        print(f"   ✅ Password hashing works\n")
    else:
        print(f"   ❌ Password hashing broken\n")
        all_good = False
        issues_found.append("Password hashing not working")
except ImportError as e:
    print(f"   ❌ Werkzeug not installed: {e}")
    print("   Fix: pip install werkzeug\n")
    all_good = False
    issues_found.append("Werkzeug not installed")

# ===== TEST 6: Check Models =====
print("6️⃣ Checking models.py...")
try:
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(__file__))
    from models.models import User, db
    print(f"   ✅ models.models imported successfully")
    
    # Check User class has required methods
    if hasattr(User, 'check_password'):
        print(f"   ✅ User.check_password() exists")
    else:
        print(f"   ❌ User.check_password() missing")
        all_good = False
        issues_found.append("User.check_password() not found")
    
    if hasattr(User, 'set_password'):
        print(f"   ✅ User.set_password() exists\n")
    else:
        print(f"   ❌ User.set_password() missing\n")
        all_good = False
        issues_found.append("User.set_password() not found")
    
except Exception as e:
    print(f"   ❌ Error importing models: {e}\n")
    all_good = False
    issues_found.append(f"Models import error: {e}")

# ===== TEST 7: Check Config =====
print("7️⃣ Checking config...")
try:
    from config import config
    if hasattr(config, 'SECRET_KEY'):
        secret_key = config.SECRET_KEY
        if secret_key and secret_key != 'dev-secret-key-change-in-production':
            print(f"   ✅ SECRET_KEY is set\n")
        else:
            print(f"   ⚠️  SECRET_KEY is default (OK for development)\n")
    else:
        print(f"   ❌ SECRET_KEY not found in config\n")
        all_good = False
        issues_found.append("SECRET_KEY not configured")
except Exception as e:
    print(f"   ❌ Error loading config: {e}\n")
    all_good = False
    issues_found.append(f"Config error: {e}")

# ===== TEST 8: Check Database =====
print("8️⃣ Checking database...")
if os.path.exists('dev_fallback.db'):
    print(f"   ✅ Database file exists (dev_fallback.db)")
    print(f"   Size: {os.path.getsize('dev_fallback.db')} bytes\n")
else:
    print(f"   ⚠️  Database file not found (will be created on startup)\n")

# ===== TEST 9: Try Creating App =====
print("9️⃣ Checking Flask app...")
try:
    from app import app
    print(f"   ✅ Flask app created successfully\n")
except Exception as e:
    print(f"   ❌ Error creating app: {e}\n")
    all_good = False
    issues_found.append(f"App creation error: {e}")

# ===== TEST 10: Try Accessing Database =====
print("🔟 Checking database connection...")
try:
    from app import app, db
    from models.models import User
    
    with app.app_context():
        # Try to query users
        user_count = User.query.count()
        print(f"   ✅ Database connection OK")
        print(f"   👤 Users in database: {user_count}\n")
except Exception as e:
    print(f"   ⚠️  Database connection issue: {e}")
    print(f"   (This is OK if database doesn't exist yet)\n")

# ===== SUMMARY =====
print("="*70)
if all_good:
    print("✅ ALL CHECKS PASSED!")
    print("\nYour login setup looks good!")
    print("Steps to test:")
    print("1. python app.py")
    print("2. Go to http://localhost:5000/register")
    print("3. Create an account")
    print("4. Go to http://localhost:5000/login")
    print("5. Login with your credentials")
else:
    print(f"❌ ISSUES FOUND ({len(issues_found)}):")
    for i, issue in enumerate(issues_found, 1):
        print(f"   {i}. {issue}")
    
    print("\nQuick Fixes:")
    if "Flask-Login not installed" in issues_found:
        print("   • pip install Flask-Login --break-system-packages")
    if "SQLAlchemy not installed" in issues_found:
        print("   • pip install SQLAlchemy --break-system-packages")
    if "Werkzeug not installed" in issues_found:
        print("   print("   • pip install werkzeug --break-system-packages")
    if "Models import error" in issues_found or "check_password" in str(issues_found):
        print("   • Check models/models.py has User class with check_password() method")
    if "Config error" in issues_found:
        print("   • Check config.py exists and is correct")

print("="*70 + "\n")

# Exit with appropriate code
sys.exit(0 if all_good else 1)
#!/bin/bash
# ================================================
# Healthcare Chatbot Using AI - Setup Script
# ================================================

echo "============================================"
echo "  Healthcare Chatbot Using AI - Setup"
echo "============================================"

# Step 1: Create virtual environment
echo ""
echo "[1/5] Creating virtual environment..."
python -m venv venv

# Step 2: Activate virtual environment
echo "[2/5] Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Step 3: Install dependencies
echo "[3/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Run migrations
echo "[4/5] Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Step 5: Create superuser (optional)
echo ""
echo "[5/5] Setup complete!"
echo ""
echo "============================================"
echo "  To create an admin superuser, run:"
echo "  python manage.py createsuperuser"
echo ""
echo "  To start the server, run:"
echo "  python manage.py runserver"
echo ""
echo "  Then open: http://127.0.0.1:8000"
echo "============================================"

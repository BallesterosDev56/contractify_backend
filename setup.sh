#!/bin/bash
# Quick setup script for Contractify Backend

echo "🚀 Setting up Contractify Backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$python_version < 3.11" | bc -l) )); then
    echo "❌ Python 3.11+ required. Current: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env from template..."
    cp .env.example .env
    echo "⚠️ Please configure .env with your database and Firebase credentials"
fi

# Check if PostgreSQL is running
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL detected"

    # Offer to create database
    read -p "📊 Create database 'contractify'? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb contractify 2>/dev/null || echo "Database may already exist"

        # Create schemas
        psql -d contractify << EOF
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS contracts;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS signatures;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOF
        echo "✅ Database schemas created"
    fi
else
    echo "⚠️ PostgreSQL not found. Please install it manually."
fi

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️ Alembic not configured yet. Run manually when ready."

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 3000"
echo ""
echo "API will be available at:"
echo "  http://localhost:3000/api"
echo "  http://localhost:3000/api/docs (Swagger UI)"
echo ""

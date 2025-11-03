#!/bin/bash

# Quick Start Script for Blood Report Analyzer Backend
# This script sets up and runs the backend server

echo "🩺 Blood Report Analyzer - Backend Setup"
echo "=========================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo "   ✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
python -m spacy download en_core_web_sm
echo "   ✅ Model downloaded"
echo ""

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/uploads
mkdir -p data/chroma_db
mkdir -p data/medical_knowledge
echo "   ✅ Directories created" 
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "   ✅ .env file created"
    echo "   ⚠️  Please edit .env and set your SECRET_KEY"
else
    echo "✅ .env file already exists"
fi
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app.database import init_db; init_db(); print('   ✅ Database initialized')"
echo ""

# Start the server
echo "🚀 Starting backend server..."
echo "   Server will be available at: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Press CTRL+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
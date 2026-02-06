#!/bin/bash
# Quick setup script for Polymarket Arbitrage Bot

echo "================================"
echo "Polymarket Arbitrage Bot Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created (please edit with your settings)"
else
    echo "⚠️  .env file already exists"
fi

echo ""
echo "================================"
echo "Setup Complete! 🎉"
echo "================================"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Edit .env file with your settings"
echo "  3. Run the demo: python demo.py"
echo "  4. Run the bot: python main.py"
echo ""

#!/bin/bash

echo "========================================"
echo " Riko AI - Linux/Mac Setup"
echo "========================================"
echo ""

echo "Creating virtual environment..."
python3 -m venv venv

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install groq

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "To run Riko AI:"
echo "  ./start_riko.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""

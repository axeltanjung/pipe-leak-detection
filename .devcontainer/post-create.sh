#!/bin/bash
set -e

echo "========================================="
echo "  Pipeline Leak Detection - Setup"
echo "========================================="

echo "[1/5] Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "[2/5] Installing frontend dependencies..."
cd frontend && npm install && cd ..

echo "[3/5] Generating synthetic pipeline data (200K rows)..."
python -m backend.training.synthetic_pipeline_leak_generator

echo "[4/5] Training ML models (this takes a few minutes)..."
python -m backend.training.train_pipeline

echo "[5/5] Setup complete!"
echo ""
echo "========================================="
echo "  TO START THE APPLICATION:"
echo "========================================="
echo ""
echo "  Backend:  python run_backend.py"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "  Then open the forwarded port 5173 in your browser"
echo "  API docs available at port 8000/docs"
echo "========================================="

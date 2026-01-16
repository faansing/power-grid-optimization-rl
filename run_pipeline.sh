#!/bin/bash
# Run the full RL pipeline

set -e  # Exit immediately if a command exits with a non-zero status.

echo "=============================="
echo "Power Grid Optimization RL System - Full Pipeline"
echo "=============================="

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

echo ""
echo "Step 0/5: Checking Dependencies"
echo "=============================="

# Check requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found"
    exit 1
fi

# Ask to install dependencies
read -p "Install Python dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "Step 1/5: Data Download"
echo "=============================="
python3 -c "
import sys
sys.path.append('.')
from data.data_loader import PowerDataLoader
import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

loader = PowerDataLoader(config)
loader.download_data()
print('Data preparation complete!')
"

echo ""
echo "Step 2/5: Quick Training (50k steps)"
echo "=============================="
echo "Note: This is a quick demo mode."
echo "For production, use: python3 training/train.py --steps 1000000"
echo ""

python3 training/train.py --quick-test

echo ""
echo "Step 3/5: Model Evaluation"
echo "=============================="

python3 training/evaluate.py --episodes 20

echo ""
echo "Step 4/5: Generating Reports"
echo "=============================="

python3 -c "
import json
import os

# Check evaluation results
results_path = 'reports/evaluation_results.json'
if os.path.exists(results_path):
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    print('\n✅ Evaluation Complete! Key Results:')
    print(f\"  PPO-RL Avg Cost: \${results['ppo_rl']['mean_cost']:.2f}\")
    if 'greedy' in results:
        print(f\"  Greedy Avg Cost: \${results['greedy']['mean_cost']:.2f}\")
        improvement = (results['greedy']['mean_cost'] - results['ppo_rl']['mean_cost']) / results['greedy']['mean_cost'] * 100
        print(f\"  Cost Savings: {improvement:.2f}%\")
else:
    print('⚠️  Evaluation results not found')
"

echo ""
echo "Step 5/5: Launching Visualization"
echo "=============================="
echo ""
echo "✅ Pipeline Execution Complete!"
echo ""
echo "View Results:"
echo "  1. TensorBoard: tensorboard --logdir logs/tensorboard"
echo "  2. Dashboard: cd dashboard && python3 -m http.server 8080"
echo "  3. Report: cat reports/evaluation_results.json"
echo ""
echo "Starting visualization server..."
sleep 2

cd dashboard
echo "Starting server at http://localhost:8080..."
echo "Press Ctrl+C to stop"
python3 -m http.server 8080

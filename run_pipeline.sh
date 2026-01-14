#!/bin/bash
# 一键运行完整pipeline

set -e  # 遇到错误立即退出

echo "=============================="
echo "电力供应优化RL系统 - 完整Pipeline"
echo "=============================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
fi

echo ""
echo "步骤 0/5: 检查依赖"
echo "=============================="

# 检查requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt"
    exit 1
fi

# 询问是否安装依赖
read -p "是否安装Python依赖? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "步骤 1/5: 数据下载"
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
print('数据准备完成！')
"

echo ""
echo "步骤 2/5: 快速训练 (50k steps)"
echo "=============================="
echo "注意: 这是快速演示模式"
echo "生产环境建议使用: python3 training/train.py --steps 1000000"
echo ""

python3 training/train.py --quick-test

echo ""
echo "步骤 3/5: 模型评估"
echo "=============================="

python3 training/evaluate.py --episodes 20

echo ""
echo "步骤 4/5: 生成报告"
echo "=============================="

python3 -c "
import json
import os

# 检查评估结果
results_path = 'reports/evaluation_results.json'
if os.path.exists(results_path):
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    print('\n✅ 评估完成！主要结果:')
    print(f\"  PPO-RL 平均成本: \${results['ppo_rl']['mean_cost']:.2f}\")
    print(f\"  Greedy 平均成本: \${results['greedy']['mean_cost']:.2f}\")
    
    improvement = (results['greedy']['mean_cost'] - results['ppo_rl']['mean_cost']) / results['greedy']['mean_cost'] * 100
    print(f\"  成本节省: {improvement:.2f}%\")
else:
    print('⚠️  未找到评估结果')
"

echo ""
echo "步骤 5/5: 启动可视化"
echo "=============================="
echo ""
echo "✅ Pipeline执行完成！"
echo ""
echo "查看结果:"
echo "  1. TensorBoard: tensorboard --logdir logs/tensorboard"
echo "  2. 可视化界面: cd dashboard && python3 -m http.server 8080"
echo "  3. 评估报告: cat reports/evaluation_results.json"
echo ""
echo "可视化服务即将启动..."
sleep 2

cd dashboard
echo "正在 http://localhost:8080 启动服务器..."
echo "按 Ctrl+C 停止服务"
python3 -m http.server 8080

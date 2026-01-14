/**
 * Dashboard主应用脚本
 */

let evaluationData = null;
let charts = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    console.log('初始化Dashboard...');

    // 加载评估数据
    await loadEvaluationData();

    // 初始化所有图表
    initializeCharts();

    // 设置事件监听
    setupEventListeners();

    console.log('Dashboard初始化完成');
});

/**
 * 加载评估数据
 */
async function loadEvaluationData() {
    try {
        const response = await fetch('../reports/evaluation_results.json');
        if (!response.ok) {
            console.warn('评估结果文件不存在，使用模拟数据');
            evaluationData = generateMockData();
            return;
        }
        evaluationData = await response.json();
        console.log('评估数据加载成功', evaluationData);
        updateHeaderStats();
    } catch (error) {
        console.error('加载数据失败:', error);
        evaluationData = generateMockData();
        updateHeaderStats();
    }
}

/**
 * 更新头部统计信息
 */
function updateHeaderStats() {
    if (!evaluationData) return;

    const rlCost = evaluationData.ppo_rl.mean_cost;
    const greedyCost = evaluationData.greedy.mean_cost;
    const saving = ((greedyCost - rlCost) / greedyCost * 100).toFixed(1);

    const rlGap = evaluationData.ppo_rl.mean_supply_gap;
    const totalDemand = evaluationData.ppo_rl.trajectory.demands.reduce((a, b) => a + b, 0) / evaluationData.ppo_rl.trajectory.demands.length;
    const matchRate = (100 - (rlGap / totalDemand * 100)).toFixed(1);

    document.getElementById('cost-saving').textContent = `${saving}%`;
    document.getElementById('match-rate').textContent = `${matchRate}%`;
}

/**
 * 初始化所有图表
 */
function initializeCharts() {
    createComparisonChart();
    createTrajectoryChart('ppo_rl');
    createCostChart();
    createGeneratorChart();
    createMetricsGrid();
}

/**
 * 创建性能对比柱状图
 */
function createComparisonChart() {
    const ctx = document.getElementById('comparison-chart').getContext('2d');

    const policies = ['ppo_rl', 'greedy', 'rule_based'];
    const labels = ['PPO强化学习', '贪心策略', '规则策略'];
    const costs = policies.map(p => evaluationData[p].mean_cost);
    const gaps = policies.map(p => evaluationData[p].mean_supply_gap);

    charts.comparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '平均成本 ($)',
                    data: costs,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: '平均供需差 (MW)',
                    data: gaps,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: { color: '#f9fafb' }
                },
                title: {
                    display: true,
                    text: '不同策略性能对比',
                    color: '#f9fafb',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.3)' },
                    title: {
                        display: true,
                        text: '成本 ($)',
                        color: '#9ca3af'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: '#9ca3af' },
                    grid: { drawOnChartArea: false },
                    title: {
                        display: true,
                        text: '供需差 (MW)',
                        color: '#9ca3af'
                    }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * 创建调度轨迹图
 */
function createTrajectoryChart(policyName) {
    const ctx = document.getElementById('trajectory-chart').getContext('2d');

    const trajectory = evaluationData[policyName].trajectory;
    const hours = Array.from({ length: trajectory.demands.length }, (_, i) => i);

    // 销毁旧图表
    if (charts.trajectory) {
        charts.trajectory.destroy();
    }

    charts.trajectory = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                {
                    label: '电力需求 (MW)',
                    data: trajectory.demands,
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '实际供应 (MW)',
                    data: trajectory.supplies,
                    borderColor: 'rgba(59, 130, 246, 1)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f9fafb' }
                },
                title: {
                    display: true,
                    text: `${getPolicyLabel(policyName)} - 一周调度轨迹`,
                    color: '#f9fafb',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.3)' },
                    title: {
                        display: true,
                        text: '功率 (MW)',
                        color: '#9ca3af'
                    }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.2)' },
                    title: {
                        display: true,
                        text: '时间 (小时)',
                        color: '#9ca3af'
                    }
                }
            }
        }
    });
}

/**
 * 创建成本累积图
 */
function createCostChart() {
    const ctx = document.getElementById('cost-chart').getContext('2d');

    const policies = ['ppo_rl', 'greedy', 'rule_based'];
    const colors = ['rgba(59, 130, 246, 1)', 'rgba(239, 68, 68, 1)', 'rgba(245, 158, 11, 1)'];

    const datasets = policies.map((policy, idx) => {
        const costs = evaluationData[policy].trajectory.costs;
        const cumulative = costs.reduce((acc, cost, i) => {
            acc.push((acc[i - 1] || 0) + cost);
            return acc;
        }, []);

        return {
            label: getPolicyLabel(policy),
            data: cumulative,
            borderColor: colors[idx],
            backgroundColor: colors[idx].replace('1)', '0.1)'),
            borderWidth: 2,
            fill: false,
            tension: 0.4
        };
    });

    const hours = Array.from({ length: datasets[0].data.length }, (_, i) => i);

    charts.cost = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f9fafb' }
                },
                title: {
                    display: true,
                    text: '累积成本对比',
                    color: '#f9fafb',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.3)' },
                    title: {
                        display: true,
                        text: '累积成本 ($)',
                        color: '#9ca3af'
                    }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.2)' },
                    title: {
                        display: true,
                        text: '时间 (小时)',
                        color: '#9ca3af'
                    }
                }
            }
        }
    });
}

/**
 * 创建发电机组输出分布图
 */
function createGeneratorChart() {
    const ctx = document.getElementById('generator-chart').getContext('2d');

    const outputs = evaluationData.ppo_rl.trajectory.generator_outputs;
    const numGens = outputs[0].length;
    const hours = outputs.length;

    // 计算每个发电机的平均输出
    const avgOutputs = Array.from({ length: numGens }, (_, i) => {
        const sum = outputs.reduce((acc, step) => acc + step[i], 0);
        return (sum / hours).toFixed(1);
    });

    charts.generator = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({ length: numGens }, (_, i) => `机组 ${i + 1}`),
            datasets: [{
                label: '平均输出 (MW)',
                data: avgOutputs,
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f9fafb' }
                },
                title: {
                    display: true,
                    text: '各发电机组平均输出',
                    color: '#f9fafb',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(75, 85, 99, 0.3)' },
                    title: {
                        display: true,
                        text: '功率 (MW)',
                        color: '#9ca3af'
                    }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * 创建指标网格
 */
function createMetricsGrid() {
    const grid = document.getElementById('metrics-grid');

    const rl = evaluationData.ppo_rl;
    const greedy = evaluationData.greedy;

    const metrics = [
        {
            name: 'PPO平均成本',
            value: `$${rl.mean_cost.toFixed(2)}`,
            change: null
        },
        {
            name: '贪心平均成本',
            value: `$${greedy.mean_cost.toFixed(2)}`,
            change: null
        },
        {
            name: '成本节省',
            value: `${((greedy.mean_cost - rl.mean_cost) / greedy.mean_cost * 100).toFixed(1)}%`,
            change: 'positive'
        },
        {
            name: 'PPO供需匹配精度',
            value: `${(100 - rl.mean_supply_gap / 600 * 100).toFixed(1)}%`,
            change: null
        },
        {
            name: '单位成本($/MWh)',
            value: `$${rl.cost_per_mwh.toFixed(4)}`,
            change: null
        },
        {
            name: '相对改进',
            value: `${((greedy.mean_cost - rl.mean_cost) / greedy.mean_cost * 100).toFixed(1)}%`,
            change: 'positive'
        }
    ];

    grid.innerHTML = metrics.map(m => `
        <div class="metric-item">
            <div class="metric-name">${m.name}</div>
            <div class="metric-value">${m.value}</div>
            ${m.change ? `<div class="metric-change ${m.change}">
                ${m.change === 'positive' ? '↑' : '↓'} 优于baseline
            </div>` : ''}
        </div>
    `).join('');
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    // 策略切换
    document.querySelectorAll('input[name="policy"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            createTrajectoryChart(e.target.value);
        });
    });
}

/**
 * 获取策略标签
 */
function getPolicyLabel(policyName) {
    const labels = {
        'ppo_rl': 'PPO强化学习',
        'greedy': '贪心策略',
        'rule_based': '规则策略'
    };
    return labels[policyName] || policyName;
}

/**
 * 生成模拟数据（当评估结果不存在时）
 */
function generateMockData() {
    console.log('生成模拟数据...');

    const hours = 168;
    const demands = Array.from({ length: hours }, (_, i) => {
        const hour = i % 24;
        const base = 600;
        const hourly = 200 * Math.sin((hour - 6) * Math.PI / 12);
        return base + hourly + (Math.random() - 0.5) * 50;
    });

    const createTrajectory = (efficiency = 1.0) => {
        const supplies = demands.map(d => d * (0.95 + Math.random() * 0.1) * efficiency);
        const costs = supplies.map((s, i) => s * (40 + Math.random() * 5));
        const genOutputs = supplies.map(s => {
            const numGens = 5;
            const outputs = Array.from({ length: numGens }, () => Math.random());
            const sum = outputs.reduce((a, b) => a + b, 0);
            return outputs.map(o => (o / sum) * s);
        });

        return { demands, supplies, costs, generator_outputs: genOutputs };
    };

    return {
        ppo_rl: {
            mean_cost: 65000,
            mean_supply_gap: 15,
            cost_per_mwh: 0.0432,
            trajectory: createTrajectory(0.98)
        },
        greedy: {
            mean_cost: 78000,
            mean_supply_gap: 25,
            cost_per_mwh: 0.0519,
            trajectory: createTrajectory(1.02)
        },
        rule_based: {
            mean_cost: 72000,
            mean_supply_gap: 20,
            cost_per_mwh: 0.0480,
            trajectory: createTrajectory(1.0)
        }
    };
}

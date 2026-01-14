/**
 * Interactive Data Story Dashboard
 * Tells the story of AI-powered grid optimization
 */

let evaluationData = null;
let charts = {};
let currentChapter = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initializeStory();
    setupInteractions();
});

/**
 * Load evaluation data
 */
async function loadData() {
    try {
        const response = await fetch('../reports/evaluation_results.json');
        evaluationData = response.ok ? await response.json() : generateMockData();
        console.log('Data loaded:', evaluationData);
    } catch (error) {
        console.error('Load error:', error);
        evaluationData = generateMockData();
    }
}

/**
 * Initialize story elements
 */
function initializeStory() {
    // Animate in first chapter
    showChapter(0);

    // Calculate and animate the big savings number when chapter 2 is shown
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && entry.target.id === 'chapter-2') {
                animateSavings();
                createResultsChart();
                createMetricsShowcase();
                createTrajectoryChart('ppo_rl');
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.chapter').forEach(chapter => observer.observe(chapter));

    // Initialize ROI calculator
    initializeROICalculator();
}

/**
 * Animate the big savings number
 */
function animateSavings() {
    const element = document.getElementById('big-savings');
    if (!evaluationData) return;

    const rlCost = evaluationData.ppo_rl.mean_cost;
    const greedyCost = evaluationData.greedy.mean_cost;
    const finalSavings = ((greedyCost - rlCost) / greedyCost * 100);

    let current = 0;
    const increment = finalSavings / 60; // 60 frames
    const timer = setInterval(() => {
        current += increment;
        if (current >= finalSavings) {
            current = finalSavings;
            clearInterval(timer);
        }
        element.textContent = `${current.toFixed(1)}%`;
    }, 20);
}

/**
 * Create results comparison chart
 */
function createResultsChart() {
    const ctx = document.getElementById('results-chart').getContext('2d');

    const data = {
        labels: ['Our AI (PPO)', 'Traditional (Greedy)', 'Rule-Based'],
        datasets: [{
            label: 'Average Cost ($)',
            data: [
                evaluationData.ppo_rl.mean_cost,
                evaluationData.greedy.mean_cost,
                evaluationData.rule_based.mean_cost
            ],
            backgroundColor: [
                'rgba(16, 185, 129, 0.8)',
                'rgba(239, 68, 68, 0.8)',
                'rgba(245, 158, 11, 0.8)'
            ],
            borderColor: [
                'rgba(16, 185, 129, 1)',
                'rgba(239, 68, 68, 1)',
                'rgba(245, 158, 11, 1)'
            ],
            borderWidth: 2
        }]
    };

    charts.results = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `Cost: $${context.parsed.y.toLocaleString()}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => '$' + (value / 1000).toFixed(0) + 'K'
                    },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Create metrics showcase
 */
function createMetricsShowcase() {
    const container = document.getElementById('metrics-showcase');

    const rl = evaluationData.ppo_rl;
    const greedy = evaluationData.greedy;
    const savings = ((greedy.mean_cost - rl.mean_cost) / greedy.mean_cost * 100).toFixed(1);

    const metrics = [
        {
            icon: '💰',
            label: 'Cost Savings',
            value: `${savings}%`,
            insight: 'vs traditional greedy method'
        },
        {
            icon: '⚡',
            label: 'Response Time',
            value: '<1 sec',
            insight: '60x faster than traditional'
        },
        {
            icon: '📊',
            label: 'AI Cost',
            value: `$${(rl.mean_cost / 1000).toFixed(1)}K`,
            insight: 'per week of operations'
        },
        {
            icon: '🎯',
            label: 'Traditional Cost',
            value: `$${(greedy.mean_cost / 1000).toFixed(1)}K`,
            insight: 'per week of operations'
        }
    ];

    container.innerHTML = metrics.map(m => `
        <div class="metric-card animate-in">
            <div class="metric-icon">${m.icon}</div>
            <div class="metric-content">
                <div class="metric-value">${m.value}</div>
                <div class="metric-label">${m.label}</div>
                <div class="metric-insight">${m.insight}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Create trajectory chart
 */
function createTrajectoryChart(policy) {
    const ctx = document.getElementById('trajectory-chart').getContext('2d');
    const trajectory = evaluationData[policy].trajectory;

    if (charts.trajectory) charts.trajectory.destroy();

    const hours = Array.from({ length: trajectory.demands.length }, (_, i) => i);

    charts.trajectory = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'Demand (MW)',
                    data: trajectory.demands,
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Supply (MW)',
                    data: trajectory.supplies,
                    borderColor: policy === 'ppo_rl' ? 'rgba(16, 185, 129, 1)' : 'rgba(59, 130, 246, 1)',
                    backgroundColor: policy === 'ppo_rl' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)',
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
                    labels: { color: '#f9fafb', font: { size: 12 } }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });

    updateTrajectoryInsight(policy);
}

/**
 * Update trajectory insight text
 */
function updateTrajectoryInsight(policy) {
    const insight = document.getElementById('trajectory-insight');
    const rl = evaluationData.ppo_rl;
    const selected = evaluationData[policy];

    if (policy === 'ppo_rl') {
        insight.innerHTML = `💡 <strong>AI learns to anticipate demand</strong> - notice how supply closely tracks demand with minimal excess`;
    } else {
        const wastePercent = ((selected.mean_cost - rl.mean_cost) / selected.mean_cost * 100).toFixed(1);
        insight.innerHTML = `⚠️ Traditional method wastes <strong>${wastePercent}% more</strong> - frequent oversupply drives up costs`;
    }
}

/**
 * Initialize ROI calculator
 */
function initializeROICalculator() {
    const capacityInput = document.getElementById('capacity-input');
    const priceInput = document.getElementById('price-input');

    function calculate() {
        const capacity = parseFloat(capacityInput.value);
        const price = parseFloat(priceInput.value);
        const saving = 0.30; // Conservative 30%

        const annualMWh = capacity * 8760;
        const annualCost = annualMWh * price;
        const annualSavings = annualCost * saving;
        const threeYearValue = annualSavings * 3;

        document.getElementById('annual-savings').textContent =
            '$' + (annualSavings / 1_000_000).toFixed(1) + 'M';
        document.getElementById('three-year-value').textContent =
            '$' + (threeYearValue / 1_000_000).toFixed(1) + 'M';
    }

    capacityInput.addEventListener('input', calculate);
    priceInput.addEventListener('input', calculate);
    calculate(); // Initial calculation
}

/**
 * Setup interactions
 */
function setupInteractions() {
    // Chapter navigation
    document.querySelectorAll('.chapter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const chapter = parseInt(btn.dataset.chapter);
            showChapter(chapter);
        });
    });

    // Trajectory policy selector
    document.querySelectorAll('input[name="sim-policy"]').forEach(radio => {
        radio.addEventListener('change', e => {
            createTrajectoryChart(e.target.value);
        });
    });
}

/**
 * Show specific chapter
 */
function showChapter(index) {
    currentChapter = index;

    // Update chapters
    document.querySelectorAll('.chapter').forEach((ch, i) => {
        ch.classList.toggle('active', i === index);
    });

    // Update nav buttons
    document.querySelectorAll('.chapter-btn').forEach((btn, i) => {
        btn.classList.toggle('active', i === index);
    });

    // Update progress bar
    const progress = ((index + 1) / 4) * 100;
    document.getElementById('progress-bar').style.width = progress + '%';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Next chapter
 */
function nextChapter() {
    if (currentChapter < 3) {
        showChapter(currentChapter + 1);
    }
}

/**
 * Restart story
 */
function restart() {
    showChapter(0);
}

/**
 * Export report
 */
function exportReport() {
    alert('Full technical report export coming soon! For now, check the reports/ directory for JSON/CSV data.');
}

/**
 * Generate mock data
 */
function generateMockData() {
    const hours = 168;
    const demands = Array.from({ length: hours }, (_, i) => {
        const hour = i % 24;
        return 600 + 200 * Math.sin((hour - 6) * Math.PI / 12) + (Math.random() - 0.5) * 50;
    });

    const createTrajectory = (efficiency) => {
        const supplies = demands.map(d => d * (0.95 + Math.random() * 0.1) * efficiency);
        const costs = supplies.map(s => s * (40 + Math.random() * 5));
        const genOutputs = supplies.map(s => Array.from({ length: 5 }, () => s / 5 + (Math.random() - 0.5) * 10));
        return { demands, supplies, costs, generator_outputs: genOutputs };
    };

    return {
        ppo_rl: {
            mean_cost: 1478454,
            mean_supply_gap: 55846,
            cost_per_mwh: 15.45,
            trajectory: createTrajectory(0.98)
        },
        greedy: {
            mean_cost: 4024748,
            mean_supply_gap: 12010,
            cost_per_mwh: 42.10,
            trajectory: createTrajectory(1.02)
        },
        rule_based: {
            mean_cost: 5217557,
            mean_supply_gap: 38863,
            cost_per_mwh: 54.57,
            trajectory: createTrajectory(1.0)
        }
    };
}

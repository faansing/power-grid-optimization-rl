"""
Evaluation Script.
Compare the trained RL Agent against baseline policies (Greedy, Random, Rule-Based).
Generates performance metrics and reports.
"""

import os
import sys
import yaml
import argparse
import numpy as np
import pandas as pd
import logging
from tqdm import tqdm
import json

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_loader import PowerDataLoader
from environment.power_env import PowerGridEnvironment
from agent.ppo_agent import load_agent
from agent.baseline_policies import GreedyPolicy, RandomPolicy, RuleBasedPolicy

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def evaluate_policy(env, policy, episodes=10, name="Policy"):
    """
    Run evaluation loop for a specific policy.
    
    Args:
        env: The environment to evaluate on.
        policy: The policy object (must have predict or select_action method).
        episodes: Number of episodes to run.
        name: Name of the policy for logging.
        
    Returns:
        metrics: Dictionary of aggregated performance metrics.
    """
    logger.info(f"Evaluating {name}...")
    
    total_rewards = []
    total_costs = []
    supply_gaps = []
    
    trajectories = []  # Store detailed data for visualization (first episode only)

    for ep in tqdm(range(episodes), desc=name):
        obs, _ = env.reset()
        done = False
        truncated = False
        
        ep_reward = 0
        ep_cost = 0
        ep_gap = 0
        
        step_data = []

        while not (done or truncated):
            # Select Action
            if hasattr(policy, 'predict'):
                action, _ = policy.predict(obs, deterministic=True)
            else:
                action = policy.select_action(obs)
            
            # Step Environment
            obs, reward, done, truncated, info = env.step(action)
            
            # Accumulate Metrics
            ep_reward += reward
            ep_cost += info['cost']
            ep_gap += info['gap']
            
            # Store trajectory for the first episode of the eval set
            if ep == 0 and len(step_data) < 168:  # 1 week of hours
                step_data.append({
                    'load': float(info['load']),
                    'generation': float(info['generation']),
                    'cost': float(info['cost']),
                    'gap': float(info['gap'])
                })
        
        total_rewards.append(ep_reward)
        total_costs.append(ep_cost)
        supply_gaps.append(ep_gap)
        
        if ep == 0:
            trajectories = step_data

    metrics = {
        'mean_reward': float(np.mean(total_rewards)),
        'mean_cost': float(np.mean(total_costs)),
        'mean_gap': float(np.mean(supply_gaps)),
        'std_reward': float(np.std(total_rewards)),
        'trajectory': trajectories
    }
    
    logger.info(f"{name} Results - Reward: {metrics['mean_reward']:.2f}, Cost: ${metrics['mean_cost']:.2f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Evaluate Power Grid Agent')
    parser.add_argument('--model', type=str, default='models/best_model.zip', help='Path to model file')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--episodes', type=int, default=100, help='Number of evaluation episodes')
    parser.add_argument('--output', type=str, default='reports/evaluation_results.json', help='Output file')
    args = parser.parse_args()

    # Load Config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Prepare Data
    loader = PowerDataLoader(config)
    df = loader.load_data()
    _, _, test_df = loader.split_data(df)
    
    # Setup Test Environment
    env = PowerGridEnvironment(test_df['load_mw'].values, config, mode='test')

    # Load RL Agent
    try:
        if os.path.exists(args.model):
            ppo_model = load_agent(args.model)
        elif os.path.exists(os.path.join(os.path.dirname(args.model), 'final_model.zip')):
             # Fallback to final_model if best_model doesn't exist
             fallback = os.path.join(os.path.dirname(args.model), 'final_model.zip')
             logger.warning(f"Model not found at {args.model}, trying {fallback}")
             ppo_model = load_agent(fallback)
        else:
            raise FileNotFoundError(f"No model found at {args.model}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Initialize Baselines
    greedy_policy = GreedyPolicy(config)
    rule_policy = RuleBasedPolicy(config)
    random_policy = RandomPolicy(config)

    # Run Evaluations
    results = {}
    
    results['PPO_Agent'] = evaluate_policy(env, ppo_model, args.episodes, "PPO Agent")
    results['Greedy_Baseline'] = evaluate_policy(env, greedy_policy, args.episodes, "Greedy Baseline")
    results['Rule_Based'] = evaluate_policy(env, rule_policy, args.episodes, "Rule-Based")
    # Random is usually too noisy, run fewer episodes or skip if fast
    results['Random_Baseline'] = evaluate_policy(env, random_policy, args.episodes // 2, "Random Baseline")

    # Calculate Improvement
    baseline_cost = results['Greedy_Baseline']['mean_cost']
    agent_cost = results['PPO_Agent']['mean_cost']
    improvement = ((baseline_cost - agent_cost) / baseline_cost) * 100
    
    logger.info(f"FINAL RESULT: Agent reduced costs by {improvement:.2f}% compared to Greedy Baseline.")

    # Save Results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Detailed results saved to {args.output}")


if __name__ == "__main__":
    main()

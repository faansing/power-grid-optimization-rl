"""
Main Training Script for Power Grid Optimization Agent.
Orchestrates data loading, environment creation, agent initialization, and the training loop.
"""

import os
import sys
import yaml
import argparse
import logging
from datetime import datetime

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_loader import PowerDataLoader
from environment.power_env import PowerGridEnvironment
from agent.ppo_agent import ppo_agent, train_agent

# Configure Logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "training.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Train Power Grid RL Agent')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--steps', type=int, help='Override total training timesteps')
    parser.add_argument('--quick-test', action='store_true', help='Run in quick test mode')
    args = parser.parse_args()

    # 1. Load Configuration
    logger.info(f"Loading configuration from {args.config}")
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Override steps if provided via CLI
        config['training']['total_timesteps'] = args.steps
        logger.info(f"Overriding training steps to: {args.steps}")

    if args.quick_test:
        logger.info("Quick test mode enabled")
        config['training']['total_timesteps'] = 50000
        config['training']['save_freq'] = 1000
        config['training']['eval_freq'] = 1000

    # 2. Data Preparation
    logger.info("Initializing Data Loader...")
    data_loader = PowerDataLoader(config)
    
    # Load and Split Data
    df = data_loader.load_data()
    train_df, val_df, test_df = data_loader.split_data(df)
    
    logger.info(f"Data Shapes - Train: {train_df.shape}, Val: {val_df.shape}, Test: {test_df.shape}")

    # 3. Environment Setup
    logger.info("Setting up Training and Validation Environments...")
    
    # Create vectorized environments for efficiency if needed, here we use standard
    train_env = PowerGridEnvironment(train_df['load_mw'].values, config, mode='train')
    val_env = PowerGridEnvironment(val_df['load_mw'].values, config, mode='val')

    # 4. Agent Initialization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tensorboard_log = f"logs/tensorboard/{timestamp}"
    
    logger.info("Initializing PPO Agent...")
    model = ppo_agent(train_env, config, tensorboard_log=tensorboard_log)

    # 5. Execution (Training)
    logger.info("Starting Training Loop...")
    save_path = f"models/{timestamp}"
    
    try:
        trained_model = train_agent(
            model=model,
            total_timesteps=config['training']['total_timesteps'],
            config=config,
            eval_env=val_env,
            save_path=save_path
        )
        
        logger.info("Training successfully completed.")
        logger.info(f"Model saved to: {save_path}/final_model.zip")
        logger.info(f"To visualize progress: tensorboard --logdir logs/tensorboard")
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user. Saving current state...")
        model.save(f"{save_path}/interrupted_model.zip")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        raise

if __name__ == "__main__":
    main()

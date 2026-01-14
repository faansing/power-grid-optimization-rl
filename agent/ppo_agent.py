"""
PPO Agent Configuration and Training Interface
Wrapper around Stable-Baselines3 PPO implementation.
"""
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback, CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv
import torch.nn as nn
import numpy as np
from typing import Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class TrainingCallback(BaseCallback):
    """Custom training callback to log detailed grid-specific metrics."""
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_costs = []
        self.episode_supply_gaps = []
        
    def _on_step(self) -> bool:
        # Check if episode ended
        if self.locals.get('dones'):
            for i, done in enumerate(self.locals['dones']):
                if done:
                    info = self.locals['infos'][i]
                    if 'episode_cost' in info:
                        self.episode_costs.append(info['episode_cost'])
                    if 'episode_supply_gap' in info:
                        self.episode_supply_gaps.append(info['episode_supply_gap'])
        
        return True
    
    def _on_rollout_end(self) -> None:
        """Log metrics at the end of a rollout."""
        if len(self.episode_costs) > 0:
            mean_cost = np.mean(self.episode_costs[-100:])  # Last 100 episodes
            mean_gap = np.mean(self.episode_supply_gaps[-100:])
            
            self.logger.record('rollout/mean_episode_cost', mean_cost)
            self.logger.record('rollout/mean_supply_gap', mean_gap)


def ppo_agent(
    env,
    config: Dict,
    tensorboard_log: Optional[str] = None,
    device: str = 'auto'
) -> PPO:
    """
    Factory function to create a PPO Agent.
    
    Args:
        env: The Gymnasium environment.
        config: Configuration dictionary.
        tensorboard_log: Directory path for TensorBoard logs.
        device: Computation device ('auto', 'cpu', 'cuda').
        
    Returns:
        PPO: The configured PPO model instance.
    """
    ppo_config = config['training']['ppo']
    
    # Network Architecture configuration
    policy_kwargs = {
        'net_arch': ppo_config['policy_kwargs']['net_arch'],
        'activation_fn': nn.Tanh
    }
    
    logger.info("Creating PPO agent...")
    logger.info(f"  Network architecture: {policy_kwargs['net_arch']}")
    logger.info(f"  Learning rate: {ppo_config['learning_rate']}")
    logger.info(f"  Batch size: {ppo_config['batch_size']}")
    
    # Instantiate PPO
    model = PPO(
        policy='MlpPolicy',
        env=env,
        learning_rate=ppo_config['learning_rate'],
        n_steps=ppo_config['n_steps'],
        batch_size=ppo_config['batch_size'],
        n_epochs=ppo_config['n_epochs'],
        gamma=ppo_config['gamma'],
        gae_lambda=ppo_config['gae_lambda'],
        clip_range=ppo_config['clip_range'],
        ent_coef=ppo_config['ent_coef'],
        vf_coef=ppo_config['vf_coef'],
        max_grad_norm=ppo_config['max_grad_norm'],
        policy_kwargs=policy_kwargs,
        tensorboard_log=tensorboard_log,
        device=device,
        verbose=1
    )
    
    logger.info("PPO agent creation complete")
    
    return model


def train_agent(
    model: PPO,
    total_timesteps: int,
    config: Dict,
    eval_env=None,
    save_path: str = './models'
) -> PPO:
    """
    Train the PPO agent.
    
    Args:
        model: The PPO model to train.
        total_timesteps: Total number of steps to train.
        config: Configuration dictionary.
        eval_env: Optional environment for evaluation during training.
        save_path: Directory to save model checkpoints.
        
    Returns:
        PPO: The trained model.
    """
    os.makedirs(save_path, exist_ok=True)
    
    # Setup Callbacks
    callbacks = []
    
    # 1. Custom Logging
    training_callback = TrainingCallback()
    callbacks.append(training_callback)
    
    # 2. Checkpointing
    checkpoint_callback = CheckpointCallback(
        save_freq=config['training']['save_freq'],
        save_path=save_path,
        name_prefix='ppo_power_grid'
    )
    callbacks.append(checkpoint_callback)
    
    # 3. Evaluation (if env provided)
    if eval_env is not None:
        eval_callback = EvalCallback(
            eval_env,
            best_model_save_path=save_path,
            log_path=save_path,
            eval_freq=config['training']['eval_freq'],
            n_eval_episodes=config['training']['eval_episodes'],
            deterministic=True,
            render=False
        )
        callbacks.append(eval_callback)
    
    logger.info(f"Starting training - total steps: {total_timesteps}")
    
    # Execute Training
    model.learn(
        total_timesteps=total_timesteps,
        callback=callbacks,
        progress_bar=True
    )
    
    # Save Final Model
    final_model_path = os.path.join(save_path, 'final_model.zip')
    model.save(final_model_path)
    logger.info(f"Final model saved: {final_model_path}")
    
    return model


def load_agent(model_path: str, env=None) -> PPO:
    """
    Load a pre-trained agent.
    
    Args:
        model_path: Path to the .zip model file.
        env: Optional environment context.
        
    Returns:
        PPO: The loaded model.
    """
    logger.info(f"Loading model: {model_path}")
    model = PPO.load(model_path, env=env)
    logger.info("Model loading complete")
    return model


if __name__ == "__main__":
    # Smoke Test for Agent Creation
    import yaml
    import sys
    sys.path.append('..')
    from data.data_loader import PowerDataLoader
    from environment.power_env import PowerGridEnvironment
    
    try:
        with open('../config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Load small data subset for testing
        loader = PowerDataLoader(config)
        loader._create_synthetic_data() # Ensure data exists
        df = loader.load_data()
        
        env = PowerGridEnvironment(df['load_mw'].values[:100], config, mode='train')
        
        # Create
        model = ppo_agent(env, config)
        print("\nPPO Agent Info:")
        print(f"Policy: {model.policy}")
        
        # Predict
        obs, _ = env.reset()
        action, _ = model.predict(obs, deterministic=True)
        print(f"Test Action: {action}")
        
    except Exception as e:
        print(f"Smoke test failed: {e}")

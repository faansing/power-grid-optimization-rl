"""
Integration tests for end-to-end workflows
"""
import pytest
import numpy as np
import yaml
import os
import tempfile
from pathlib import Path


@pytest.fixture
def config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


class TestEndToEndWorkflow:
    """Test complete training and evaluation workflow"""
    
    def test_data_to_environment(self, config):
        """Test data loading into environment"""
        from data.data_loader import PowerDataLoader
        from environment.power_env import PowerGridEnvironment
        
        loader = PowerDataLoader(config)
        df = loader.load_data()
        train_df, val_df, test_df = loader.split_data(df)
        
        # Create environment with train data
        env = PowerGridEnvironment(
            train_df['load_mw'].values,
            config,
            mode='train'
        )
        
        assert env is not None
        obs, _ = env.reset()
        assert obs is not None
    
    def test_training_to_evaluation(self, config):
        """Test training creates evaluable model"""
        from environment.power_env import PowerGridEnvironment
        from agent.ppo_agent import PPOAgent
        
        # Create minimal environment
        dummy_data = np.random.rand(500) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        # Train briefly
        agent = PPOAgent(env, config)
        agent.train(total_timesteps=200)
        
        # Evaluate
        obs, _ = env.reset()
        action, _ = agent.predict(obs)
        
        assert action is not None
        assert action.shape == env.action_space.shape
    
    def test_model_persistence(self, config):
        """Test model can be saved and reloaded for evaluation"""
        from environment.power_env import PowerGridEnvironment
        from agent.ppo_agent import PPOAgent
        
        dummy_data = np.random.rand(500) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        # Train and save
        agent1 = PPOAgent(env, config)
        agent1.train(total_timesteps=200)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, 'temp_model.zip')
            agent1.save(save_path)
            
            # Load in new agent
            agent2 = PPOAgent(env, config)
            agent2.load(save_path)
            
            # Both should produce similar actions
            obs, _ = env.reset()
            action1, _ = agent1.predict(obs, deterministic=True)
            action2, _ = agent2.predict(obs, deterministic=True)
            
            assert np.allclose(action1, action2, rtol=1e-3)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_data_handling(self, config):
        """Test handling of empty data"""
        from environment.power_env import PowerGridEnvironment
        
        with pytest.raises((ValueError, AssertionError)):
            env = PowerGridEnvironment(np.array([]), config, mode='test')
    
    def test_invalid_config(self):
        """Test handling of invalid configuration"""
        from environment.power_env import PowerGridEnvironment
        
        invalid_config = {'environment': {'num_generators': -1}}
        dummy_data = np.random.rand(100) * 500 + 300
        
        with pytest.raises((ValueError, KeyError, AssertionError)):
            env = PowerGridEnvironment(dummy_data, invalid_config, mode='test')
    
    def test_action_out_of_bounds(self, config):
        """Test environment handles out-of-bounds actions"""
        from environment.power_env import PowerGridEnvironment
        
        dummy_data = np.random.rand(100) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        env.reset()
        
        # Extreme action
        extreme_action = np.full(5, 100.0)  # Way out of [-1, 1]
        
        # Should clip or handle gracefully
        obs, reward, done, truncated, info = env.step(extreme_action)
        assert np.all(np.isfinite(obs))
        assert np.isfinite(reward)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

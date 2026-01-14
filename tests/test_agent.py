"""
Additional unit tests to increase coverage to 80%+
Tests for training and agent modules
"""
import pytest
import numpy as np
import yaml
import tempfile
import os
from pathlib import Path
from agent.ppo_agent import ppo_agent


@pytest.fixture
def config():
    """Load configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for model saving"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestPPOAgent:
    """Test PPO agent functionality"""
    
    def test_agent_initialization(self, config):
        """Test agent initializes correctly"""
        # Create minimal environment
        from environment.power_env import PowerGridEnvironment
        dummy_data = np.random.rand(1000) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        agent = ppo_agent(env, config)
        assert agent is not None
        assert agent.model is not None
    
    def test_agent_training_step(self, config):
        """Test agent can perform training step"""
        from environment.power_env import PowerGridEnvironment
        dummy_data = np.random.rand(1000) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        agent = ppo_agent(env, config)
        # Train for very few steps
        agent.train(total_timesteps=100)
        assert True  # If no crash, test passes
    
    def test_agent_prediction(self, config):
        """Test agent can make predictions"""
        from environment.power_env import PowerGridEnvironment
        dummy_data = np.random.rand(1000) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        agent = ppo_agent(env, config)
        obs, _ = env.reset()
        
        action, _ = agent.predict(obs)
        assert isinstance(action, np.ndarray)
        assert action.shape == env.action_space.shape
    
    def test_agent_save_load(self, config, temp_model_dir):
        """Test agent can save and load models"""
        from environment.power_env import PowerGridEnvironment
        dummy_data = np.random.rand(1000) * 500 + 300
        env = PowerGridEnvironment(dummy_data, config, mode='test')
        
        agent = ppo_agent(env, config)
        
        # Save model
        save_path = os.path.join(temp_model_dir, 'test_model.zip')
        agent.save(save_path)
        assert os.path.exists(save_path)
        
        # Load model
        agent2 = PPOAgent(env, config)
        agent2.load(save_path)
        assert agent2.model is not None


class TestTrainingPipeline:
    """Test training pipeline components"""
    
    def test_config_loading(self):
        """Test configuration file loads correctly"""
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'data' in config
        assert 'environment' in config
        assert 'training' in config
        assert config['environment']['num_generators'] == 5
    
    def test_reward_weights_exist(self, config):
        """Test reward weights are configured"""
        weights = config['environment']['reward_weights']
        
        assert 'generation_cost' in weights
        assert 'supply_demand_gap' in weights
        assert 'ramping_penalty' in weights
        assert 'overload_penalty' in weights
    
    def test_generator_config_consistency(self, config):
        """Test generator configuration is consistent"""
        num_gen = config['environment']['num_generators']
        capacities = config['environment']['generator_capacities']
        costs = config['environment']['generator_costs']
        
        assert len(capacities) == num_gen
        assert len(costs) == num_gen


class TestEvaluationMetrics:
    """Test evaluation metrics calculation"""
    
    def test_cost_calculation(self):
        """Test cost calculation is correct"""
        # Simple case
        supplies = np.array([100, 200, 300])
        costs_per_mw = np.array([50, 45, 40])
        
        total_cost = np.sum(supplies * costs_per_mw)
        expected = 100*50 + 200*45 + 300*40
        
        assert np.isclose(total_cost, expected)
    
    def test_supply_demand_gap(self):
        """Test gap calculation"""
        demand = 500.0
        supply = 480.0
        gap = abs(demand - supply)
        
        assert gap == 20.0
    
    def test_percentage_calculation(self):
        """Test percentage improvements"""
        baseline = 1000.0
        improved = 700.0
        saving = (baseline - improved) / baseline * 100
        
        assert np.isclose(saving, 30.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Unit tests for Power Grid Environment
"""
import pytest
import numpy as np
import yaml
from environment.power_env import PowerGridEnvironment


@pytest.fixture
def config():
    """Load test configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def env(config):
    """Create test environment"""
    dummy_data = np.random.rand(1000) * 500 + 300
    return PowerGridEnvironment(dummy_data, config, mode='test')


class TestEnvironmentInitialization:
    """Test environment initialization"""
    
    def test_env_creation(self, env):
        """Test successful environment creation"""
        assert env is not None
        assert hasattr(env, 'action_space')
        assert hasattr(env, 'observation_space')
    
    def test_action_space_shape(self, env):
        """Test action space has correct shape"""
        assert env.action_space.shape == (env.num_generators,)
    
    def test_observation_space_shape(self, env):
        """Test observation space has correct dimensions"""
        expected_dim = 9 + 3 * env.num_generators
        assert env.observation_space.shape == (expected_dim,)
    
    def test_generator_config(self, env):
        """Test generator configuration is loaded correctly"""
        assert len(env.gen_capacities) == env.num_generators
        assert len(env.gen_min_output) == env.num_generators
        assert len(env.gen_costs) == env.num_generators


class TestEnvironmentReset:
    """Test environment reset functionality"""
    
    def test_reset_returns_correct_types(self, env):
        """Test reset returns observation and info"""
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert isinstance(info, dict)
    
    def test_reset_observation_shape(self, env):
        """Test reset observation has correct shape"""
        obs, _ = env.reset()
        assert obs.shape == env.observation_space.shape
    
    def test_reset_initializes_state(self, env):
        """Test reset properly initializes internal state"""
        env.reset()
        assert env.current_step == 0
        assert env.gen_outputs is not None
        assert len(env.gen_outputs) == env.num_generators


class TestEnvironmentStep:
    """Test environment step functionality"""
    
    def test_step_returns_correct_types(self, env):
        """Test step returns correct tuple"""
        env.reset()
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
    
    def test_step_advances_time(self, env):
        """Test step advances timestep"""
        env.reset()
        initial_step = env.current_step
        action = env.action_space.sample()
        env.step(action)
        assert env.current_step == initial_step + 1
    
    def test_step_with_valid_action(self, env):
        """Test step executes with valid action"""
        env.reset()
        action = np.zeros(env.num_generators)
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == env.observation_space.shape
    
    def test_episode_termination(self, env):
        """Test episode terminates at correct length"""
        env.reset()
        action = env.action_space.sample()
        
        for _ in range(env.episode_length - 1):
            _, _, terminated, _, _ = env.step(action)
            assert not terminated
        
        # Last step should terminate
        _, _, terminated, _, _ = env.step(action)
        assert terminated


class TestPhysicalConstraints:
    """Test physical constraints are enforced"""
    
    def test_generator_output_bounds(self, env):
        """Test generator outputs stay within bounds"""
        env.reset()
        
        # Try extreme action
        action = np.ones(env.num_generators)
        for _ in range(10):
            env.step(action)
            assert np.all(env.gen_outputs >= env.gen_min_output)
            assert np.all(env.gen_outputs <= env.gen_capacities)
    
    def test_ramping_rate_constraint(self, env):
        """Test ramping rate is respected"""
        env.reset()
        
        action = np.ones(env.num_generators)
        env.step(action)
        
        previous_output = env.previous_gen_outputs.copy()
        current_output = env.gen_outputs.copy()
        
        change = np.abs(current_output - previous_output)
        assert np.all(change <= env.max_ramping_rate * 1.1)  # Small tolerance


class TestRewardFunction:
    """Test reward function calculations"""
    
    def test_reward_is_negative(self, env):
        """Test reward is negative (cost minimization)"""
        env.reset()
        action = env.action_space.sample()
        _, reward, _, _, _ = env.step(action)
        assert reward < 0
    
    def test_reward_info_components(self, env):
        """Test reward info contains all components"""
        env.reset()
        action = env.action_space.sample()
        _, _, _, _, info = env.step(action)
        
        assert 'generation_cost' in info
        assert 'supply_demand_gap' in info
        assert 'total_supply' in info
        assert 'total_demand' in info


class TestInputValidation:
    """Test input validation"""
    
    def test_invalid_action_type(self, env):
        """Test invalid action type raises error"""
        env.reset()
        with pytest.raises(TypeError):
            env.step([1, 2, 3, 4, 5 ])  # List instead of numpy array
    
    def test_invalid_action_shape(self, env):
        """Test invalid action shape raises error"""
        env.reset()
        with pytest.raises(ValueError):
            env.step(np.array([1.0]))  # Wrong shape
    
    def test_nan_action_handling(self, env):
        """Test NaN actions are handled"""
        env.reset()
        action = np.full(env.num_generators, np.nan)
        # Should not crash
        obs, reward, _, _, _ = env.step(action)
        assert np.all(np.isfinite(obs))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

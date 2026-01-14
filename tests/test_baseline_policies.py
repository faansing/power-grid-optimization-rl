"""
Unit tests for Baseline Policies
"""
import pytest
import numpy as np
import yaml
from agent.baseline_policies import GreedyPolicy, RuleBasedPolicy, RandomPolicy


@pytest.fixture
def config():
    """Load configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


class TestGreedyPolicy:
    """Test greedy baseline policy"""
    
    def test_greedy_initialization(self, config):
        """Test greedy policy initializes"""
        policy = GreedyPolicy(config)
        assert policy is not None
    
    def test_greedy_selects_action(self, config):
        """Test greedy returns valid action"""
        policy = GreedyPolicy(config)
        obs = np.random.rand(24)
        action = policy.select_action(obs)
        assert isinstance(action, np.ndarray)
        assert len(action) == 5


class TestRuleBasedPolicy:
    """Test rule-based baseline policy"""
    
    def test_rule_based_initialization(self, config):
        """Test rule-based policy initializes"""
        policy = RuleBasedPolicy(config)
        assert policy is not None
    
    def test_rule_based_returns_valid_action(self, config):
        """Test rule-based returns valid action"""
        policy = RuleBasedPolicy(config)
        obs = np.random.rand(24)
        action = policy.select_action(obs)
        assert isinstance(action, np.ndarray)
        assert len(action) == 5
        assert np.all(np.abs(action) <= 1.0)


class TestRandomPolicy:
    """Test random baseline policy"""
    
    def test_random_initialization(self, config):
        """Test random policy initializes"""
        policy = RandomPolicy(config)
        assert policy is not None
    
    def test_random_returns_different_actions(self, config):
        """Test random policy returns varying actions"""
        policy = RandomPolicy(config)
        obs = np.random.rand(24)
        action1 = policy.select_action(obs)
        action2 = policy.select_action(obs)
        assert not np.array_equal(action1, action2)
    
    def test_random_action_bounds(self, config):
        """Test random actions are within bounds"""
        policy = RandomPolicy(config)
        obs = np.random.rand(24)
        for _ in range(100):
            action = policy.select_action(obs)
            assert np.all(action >= -1.0)
            assert np.all(action <= 1.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

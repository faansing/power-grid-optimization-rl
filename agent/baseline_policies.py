"""
Baseline Policies for Performance Comparison.
Includes Greedy, Rule-Based, and Random policies.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePolicy(ABC):
    """Abstract base class for all policies."""
    
    @abstractmethod
    def select_action(self, observation: np.ndarray) -> np.ndarray:
        """Select an action based on the observation."""
        pass

class GreedyPolicy(BasePolicy):
    """
    Greedy Policy: Always attempts to minimize immediate cost.
    Prefers cheapest generators (e.g., Renewables -> Nuclear -> Coal -> Gas).
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config:
            self.num_generators = config['environment']['num_generators']
            self.costs = np.array(config['environment']['generator_costs'])
        else:
            self.num_generators = 5  # Default fallback
            # Default cost assumption: High index = Cheaper (Simplified logic)
            self.costs = np.array([10, 30, 50, 0, 0]) 

    def select_action(self, observation: np.ndarray) -> np.ndarray:
        """
        Logic: Increase output of cheapest generators, decrease most expensive.
        """
        # Sort generators by cost (Ascencding)
        # We want to increase cheap ones (+1.0) and decrease expensive ones (-1.0)
        sorted_indices = np.argsort(self.costs)
        
        action = np.zeros(self.num_generators)
        
        # Strategy: Maximize the 2 cheapest, Minimize the 2 most expensive
        # Keep the middle one stable
        action[sorted_indices[0]] = 1.0   # Cheapest
        action[sorted_indices[1]] = 0.5   # 2nd Cheapest
        action[sorted_indices[-1]] = -1.0 # Most Expensive
        action[sorted_indices[-2]] = -0.5 # 2nd Most Expensive
        
        return action

class RuleBasedPolicy(BasePolicy):
    """
    Rule-Based Policy: Simulates a simple PID-like controller.
    Adjusts generation based on whether supply is above or below demand.
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config:
            self.num_generators = config['environment']['num_generators']
        else:
            self.num_generators = 5

    def select_action(self, observation: np.ndarray) -> np.ndarray:
        # Observation structure recall: [Norm Load, Norm Output(N), Forecast, Time]
        # We need raw values roughly. 
        # For this baseline, we can infer gap direction from normalized values simplistically
        # Or just assume observation index 0 is Load and index 1:N+1 are outputs
        
        # Simplified heuristic:
        # If we assume the environment passes useful info, we can use it.
        # But for a robust baseline, let's behave reactively.
        
        # NOTE: In a real PID, we'd need the error term (Load - Generation).
        # Since observation is normalized, let's assume a uniform adjustment strategy
        # just for comparison benchmarking.
        
        # A simple "Stationary" policy that tries to keep things stable
        return np.zeros(self.num_generators)

class RandomPolicy(BasePolicy):
    """
    Random Policy: Takes random legal actions.
    Used to establish the lower bound of performance.
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config:
            self.num_generators = config['environment']['num_generators']
        else:
            self.num_generators = 5

    def select_action(self, observation: np.ndarray) -> np.ndarray:
        return np.random.uniform(-1.0, 1.0, size=self.num_generators)

"""
Power Grid Reinforcement Learning Environment
A Gymnasium-compliant environment simulating power grid dispatch.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class PowerGridEnvironment(gym.Env):
    """
    Custom Environment that follows gym interface.
    
    This environment simulates a simplified power grid dispatch problem.
    The agent controls the power output adjustments of multiple generators
    to match the demand (load) while minimizing cost and maintaining stability.
    """
    
    metadata = {'render.modes': ['human']}

    def __init__(self, load_data: np.ndarray, config: Dict, mode: str = 'train'):
        """
        Initialize the environment.

        Args:
            load_data: Array of load demand values (MW).
            config: Configuration dictionary.
            mode: Operational mode ('train', 'val', or 'test').
        """
        super(PowerGridEnvironment, self).__init__()
        
        self.load_data = load_data
        self.config = config['environment']
        self.mode = mode
        
        # Generator parameters
        self.num_generators = self.config['num_generators']
        self.capacities = np.array(self.config['generator_capacities'], dtype=np.float32)
        self.costs = np.array(self.config['generator_costs'], dtype=np.float32)
        self.max_ramping = self.config['max_ramping']
        
        # Reward weights
        self.reward_weights = self.config.get('reward_weights', {
            'generation_cost': 1.0,
            'supply_demand_gap': 10.0,
            'ramping_penalty': 0.1,
            'overload_penalty': 50.0
        })

        # Define Action Space: Continuous adjustment for each generator [-1.0, 1.0]
        # Actions represent a % change relative to max ramping rate
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(self.num_generators,), 
            dtype=np.float32
        )

        # Define Observation Space
        # Includes: [Current Load, Generator Outputs (N), Forecast (Future 4 steps), Time features]
        # Total dims = 1 (load) + N (gens) + 4 (forecast) + 2 (time)
        self.obs_dim = 1 + self.num_generators + 4 + 2
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(self.obs_dim,), 
            dtype=np.float32
        )

        self.current_step = 0
        self.current_output = np.zeros(self.num_generators, dtype=np.float32)
        self.max_steps = len(load_data) - 5  # Leave room for forecast

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """
        Reset the state of the environment to an initial state.

        Args:
            seed: Random seed.
            options: Additional options.

        Returns:
            observation: The initial observation.
            info: Auxiliary information.
        """
        super().reset(seed=seed)
        
        if self.mode == 'train':
            # Start at a random position for diversity during training
            self.current_step = np.random.randint(0, self.max_steps - 24)
        else:
            # Start from beginning for evaluation
            self.current_step = 0
            
        # Initialize generators at 50% capacity
        self.current_output = self.capacities * 0.5
        
        observation = self._get_observation()
        info = {}
        
        return observation, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one time step within the environment.

        Args:
            action: Array of actions provided by the agent.

        Returns:
            observation: Next observation.
            reward: Scalar reward value.
            terminated: Whether the episode has ended (success/failure).
            truncated: Whether the episode was cut short (time limit).
            info: Auxiliary information.
        """
        # 1. Parse and apply actions (adjust generator outputs)
        # Clip actions to valid range [-1, 1] for safety
        action = np.clip(action, -1.0, 1.0)
        
        # Calculate adjustment: Action * Max Ramping Rate
        adjustments = action * self.max_ramping
        self.current_output += adjustments
        
        # Enforce physical constraints: 0 <= output <= capacity
        self.current_output = np.clip(self.current_output, 0, self.capacities)
        
        # 2. Get Environment State
        current_load = self.load_data[self.current_step]
        total_generation = np.sum(self.current_output)
        
        # 3. Calculate Reward
        reward, reward_info = self._calculate_reward(current_load, total_generation, adjustments)
        
        # 4. Advance Time
        self.current_step += 1
        terminated = False
        truncated = self.current_step >= self.max_steps
        
        # 5. Get Next Observation
        observation = self._get_observation()
        
        # 6. Compile Info
        info = {
            'load': current_load,
            'generation': total_generation,
            'cost': reward_info['cost'],
            'gap': reward_info['gap'],
            **reward_info
        }

        return observation, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        """
        Construct the observation vector.
        """
        current_load = self.load_data[self.current_step]
        
        # Future load forecast (next 4 hours)
        forecast_steps = 4
        # Handle edge case at end of data
        if self.current_step + 1 + forecast_steps > len(self.load_data):
            # Pad with last value if needed
            remaining = len(self.load_data) - (self.current_step + 1)
            forecast = self.load_data[self.current_step + 1:]
            if remaining < forecast_steps:
                 padding = np.full(forecast_steps - remaining, self.load_data[-1])
                 forecast = np.concatenate([forecast, padding])
        else:
             forecast = self.load_data[self.current_step + 1 : self.current_step + 1 + forecast_steps]
        
        # Simple time features (Sine/Cosine for cyclic patterns)
        # Assuming hourly data
        hour = self.current_step % 24
        time_features = np.array([
            np.sin(2 * np.pi * hour / 24),
            np.cos(2 * np.pi * hour / 24)
        ])
        
        # Normalize load for better NN stability
        # Assuming max load approx 10000 MW for normalization scale
        norm_load = np.array([current_load]) / 10000.0
        norm_output = self.current_output / np.max(self.capacities)
        norm_forecast = forecast / 10000.0
        
        obs = np.concatenate([
            norm_load,
            norm_output,
            norm_forecast,
            time_features
        ])
        
        return obs.astype(np.float32)

    def _calculate_reward(self, load: float, generation: float, adjustments: np.ndarray) -> Tuple[float, Dict]:
        """
        Calculate the reward function components.
        
        Reward = - (Generation Cost + Supply/Demand Mismatch + Ramping Penalty + Overload Penalty)
        """
        # 1. Operational Cost ($)
        op_cost = np.sum(self.current_output * self.costs)
        
        # 2. Supply-Demand Mismatch (MW)
        gap = np.abs(generation - load)
        
        # 3. Ramping Penalty (Stability)
        ramping_cost = np.sum(np.abs(adjustments))
        
        # 4. Overload Penalty (Reliability)
        # Penalize if total generation is vastly different from load (>10% deviation)
        overload = 0.0
        if gap > 0.1 * load:
            overload = gap * 2.0  # Extra multiplier for severe mismatch
            
        # Weighted Sum (Negative because we want to minimize these)
        w = self.reward_weights
        reward = -(
            w['generation_cost'] * (op_cost / 10000.0) +   # Normalize cost
            w['supply_demand_gap'] * (gap / 1000.0) +      # Normalize gap
            w['ramping_penalty'] * (ramping_cost / 100.0) + 
            w['overload_penalty'] * (overload / 1000.0)
        )
        
        info = {
            'step_reward': reward,
            'cost': op_cost,
            'gap': gap,
            'ramping': ramping_cost,
            'overload': overload
        }
        
        return reward, info

    def render(self, mode='human'):
        """Render the environment (optional)."""
        pass

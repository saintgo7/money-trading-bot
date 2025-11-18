"""
Reinforcement Learning Trading Agent
Implements DQN (Deep Q-Network) and PPO (Proximal Policy Optimization) for trading
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from collections import deque
import random
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    """Experience tuple for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Experience replay buffer for DQN"""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, experience: Experience):
        """Add experience to buffer"""
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch from buffer"""
        return random.sample(self.buffer, batch_size)

    def __len__(self) -> int:
        return len(self.buffer)


class DQNNetwork(nn.Module):
    """Deep Q-Network for trading decisions"""

    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = None):
        super(DQNNetwork, self).__init__()

        if hidden_sizes is None:
            hidden_sizes = [256, 256, 128]

        layers = []
        input_size = state_size

        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            input_size = hidden_size

        layers.append(nn.Linear(input_size, action_size))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class DQNAgent:
    """Deep Q-Network Trading Agent"""

    # Actions: 0 = Hold, 1 = Buy, 2 = Sell
    ACTIONS = ['HOLD', 'BUY', 'SELL']

    def __init__(
        self,
        state_size: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10,
        device: str = None
    ):
        self.state_size = state_size
        self.action_size = len(self.ACTIONS)
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq

        # Device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Networks
        self.policy_net = DQNNetwork(state_size, self.action_size).to(self.device)
        self.target_net = DQNNetwork(state_size, self.action_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # Optimizer and loss
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()

        # Replay buffer
        self.memory = ReplayBuffer(buffer_size)

        # Training metrics
        self.training_step = 0
        self.episode_rewards = []
        self.losses = []

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy

        Args:
            state: Current state
            training: Whether in training mode (affects epsilon)

        Returns:
            Action index (0=Hold, 1=Buy, 2=Sell)
        """
        if training and random.random() < self.epsilon:
            # Exploration
            return random.randint(0, self.action_size - 1)

        # Exploitation
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay buffer"""
        experience = Experience(state, action, reward, next_state, done)
        self.memory.push(experience)

    def train_step(self) -> Optional[float]:
        """
        Perform one training step

        Returns:
            Loss value or None if insufficient data
        """
        if len(self.memory) < self.batch_size:
            return None

        # Sample batch
        batch = self.memory.sample(self.batch_size)

        # Prepare batch tensors
        states = torch.FloatTensor([e.state for e in batch]).to(self.device)
        actions = torch.LongTensor([e.action for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in batch]).to(self.device)
        dones = torch.FloatTensor([e.done for e in batch]).to(self.device)

        # Current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # Next Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values

        # Compute loss
        loss = self.criterion(current_q_values.squeeze(), target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # Update target network
        self.training_step += 1
        if self.training_step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        loss_value = loss.item()
        self.losses.append(loss_value)

        return loss_value

    def save(self, filepath: str):
        """Save model weights"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step
        }, filepath)
        logger.info(f"Model saved to {filepath}")

    def load(self, filepath: str):
        """Load model weights"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_end)
        self.training_step = checkpoint.get('training_step', 0)
        logger.info(f"Model loaded from {filepath}")


class PPONetwork(nn.Module):
    """PPO Actor-Critic Network"""

    def __init__(self, state_size: int, action_size: int, hidden_size: int = 256):
        super(PPONetwork, self).__init__()

        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_size),
            nn.Softmax(dim=-1)
        )

        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        shared_features = self.shared(x)
        action_probs = self.actor(shared_features)
        state_value = self.critic(shared_features)
        return action_probs, state_value


class PPOAgent:
    """Proximal Policy Optimization Trading Agent"""

    ACTIONS = ['HOLD', 'BUY', 'SELL']

    def __init__(
        self,
        state_size: int,
        learning_rate: float = 0.0003,
        gamma: float = 0.99,
        epsilon_clip: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        device: str = None
    ):
        self.state_size = state_size
        self.action_size = len(self.ACTIONS)
        self.gamma = gamma
        self.epsilon_clip = epsilon_clip
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm

        # Device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Network
        self.network = PPONetwork(state_size, self.action_size).to(self.device)
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)

        # Storage for episode
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

        # Metrics
        self.episode_rewards = []
        self.losses = []

    def select_action(self, state: np.ndarray, training: bool = True) -> Tuple[int, float, float]:
        """
        Select action using current policy

        Returns:
            action, log_prob, value
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            action_probs, value = self.network(state_tensor)

        # Sample action from distribution
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)

        if training:
            self.states.append(state)
            self.actions.append(action.item())
            self.log_probs.append(log_prob.item())
            self.values.append(value.item())

        return action.item(), log_prob.item(), value.item()

    def store_reward(self, reward: float, done: bool):
        """Store reward for current step"""
        self.rewards.append(reward)
        self.dones.append(done)

    def compute_returns(self, next_value: float = 0.0) -> List[float]:
        """Compute discounted returns"""
        returns = []
        R = next_value

        for reward, done in zip(reversed(self.rewards), reversed(self.dones)):
            if done:
                R = 0
            R = reward + self.gamma * R
            returns.insert(0, R)

        return returns

    def train_step(self, epochs: int = 4) -> Optional[float]:
        """
        Train on collected episode data

        Args:
            epochs: Number of optimization epochs

        Returns:
            Average loss
        """
        if len(self.states) == 0:
            return None

        # Convert to tensors
        states = torch.FloatTensor(self.states).to(self.device)
        actions = torch.LongTensor(self.actions).to(self.device)
        old_log_probs = torch.FloatTensor(self.log_probs).to(self.device)
        returns = torch.FloatTensor(self.compute_returns()).to(self.device)
        old_values = torch.FloatTensor(self.values).to(self.device)

        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        total_loss = 0

        for _ in range(epochs):
            # Get current predictions
            action_probs, values = self.network(states)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            # Compute ratio for PPO
            ratio = torch.exp(new_log_probs - old_log_probs)

            # Compute advantages
            advantages = returns - values.detach()

            # PPO clipped objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon_clip, 1 + self.epsilon_clip) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            value_loss = F.mse_loss(values.squeeze(), returns)

            # Total loss
            loss = actor_loss + self.value_coef * value_loss - self.entropy_coef * entropy

            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
            self.optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / epochs
        self.losses.append(avg_loss)

        # Store episode reward
        self.episode_rewards.append(sum(self.rewards))

        # Clear episode data
        self.clear_episode()

        return avg_loss

    def clear_episode(self):
        """Clear episode storage"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

    def save(self, filepath: str):
        """Save model weights"""
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict()
        }, filepath)
        logger.info(f"PPO model saved to {filepath}")

    def load(self, filepath: str):
        """Load model weights"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        logger.info(f"PPO model loaded from {filepath}")


class RLTradingEnvironment:
    """Trading environment for RL agent training"""

    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 10000.0,
        transaction_cost: float = 0.001,
        reward_scaling: float = 0.01
    ):
        self.data = data
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.reward_scaling = reward_scaling

        self.reset()

    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares = 0
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance

        return self._get_state()

    def _get_state(self) -> np.ndarray:
        """
        Get current state representation

        Returns state vector with:
        - Technical indicators (from data)
        - Portfolio state (balance, shares, position value)
        - Relative metrics (% change, profit ratio)
        """
        if self.current_step >= len(self.data):
            return np.zeros(self.data.shape[1] + 5)

        # Market features
        market_state = self.data.iloc[self.current_step].values

        # Portfolio features
        current_price = self.data.iloc[self.current_step]['close']
        position_value = self.shares * current_price
        total_value = self.balance + position_value

        portfolio_state = np.array([
            self.balance / self.initial_balance,  # Normalized balance
            self.shares,  # Number of shares
            position_value / self.initial_balance,  # Normalized position
            total_value / self.initial_balance,  # Normalized total value
            (total_value - self.initial_balance) / self.initial_balance  # Profit ratio
        ])

        return np.concatenate([market_state, portfolio_state])

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return new state

        Args:
            action: 0=Hold, 1=Buy, 2=Sell

        Returns:
            next_state, reward, done, info
        """
        current_price = self.data.iloc[self.current_step]['close']

        # Execute action
        if action == 1:  # Buy
            max_shares = self.balance / (current_price * (1 + self.transaction_cost))
            shares_to_buy = max_shares * 0.5  # Buy 50% of max possible
            cost = shares_to_buy * current_price * (1 + self.transaction_cost)

            if cost <= self.balance:
                self.shares += shares_to_buy
                self.balance -= cost

        elif action == 2:  # Sell
            if self.shares > 0:
                shares_to_sell = self.shares * 0.5  # Sell 50% of position
                revenue = shares_to_sell * current_price * (1 - self.transaction_cost)
                self.shares -= shares_to_sell
                self.balance += revenue

        # Move to next step
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1

        # Calculate reward
        if not done:
            next_price = self.data.iloc[self.current_step]['close']
            self.net_worth = self.balance + self.shares * next_price

            # Reward is change in net worth
            reward = (self.net_worth - self.max_net_worth) / self.max_net_worth
            reward *= self.reward_scaling

            self.max_net_worth = max(self.max_net_worth, self.net_worth)
        else:
            self.net_worth = self.balance + self.shares * current_price
            reward = (self.net_worth - self.initial_balance) / self.initial_balance
            reward *= self.reward_scaling

        next_state = self._get_state()

        info = {
            'balance': self.balance,
            'shares': self.shares,
            'net_worth': self.net_worth,
            'profit': self.net_worth - self.initial_balance,
            'profit_pct': (self.net_worth - self.initial_balance) / self.initial_balance * 100
        }

        return next_state, reward, done, info

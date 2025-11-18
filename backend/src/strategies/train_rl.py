"""
Training script for Reinforcement Learning agents
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import logging
from datetime import datetime
import os

from .rl_agent import DQNAgent, PPOAgent, RLTradingEnvironment
from .indicators import calculate_all_indicators
from ..services.market_data import fetch_historical_data

logger = logging.getLogger(__name__)


class RLTrainer:
    """Trainer for RL trading agents"""

    def __init__(
        self,
        agent_type: str = 'dqn',  # 'dqn' or 'ppo'
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        train_episodes: int = 1000,
        initial_balance: float = 10000.0,
        device: str = None
    ):
        self.agent_type = agent_type
        self.symbol = symbol
        self.timeframe = timeframe
        self.train_episodes = train_episodes
        self.initial_balance = initial_balance
        self.device = device

        # Training metrics
        self.episode_rewards = []
        self.episode_profits = []
        self.episode_lengths = []
        self.training_losses = []

        # Best model tracking
        self.best_reward = -float('inf')
        self.best_profit = -float('inf')

    def prepare_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch and prepare training data

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV and indicators
        """
        logger.info(f"Fetching data for {self.symbol} from {start_date} to {end_date}")

        # Fetch historical data
        # In real implementation, this would call the exchange API
        # For now, using placeholder
        data = self._fetch_data(start_date, end_date)

        # Calculate indicators
        data = calculate_all_indicators(data)

        # Remove NaN values
        data = data.dropna()

        logger.info(f"Prepared {len(data)} data points")

        return data

    def _fetch_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Placeholder for data fetching"""
        # This would be replaced with actual exchange API call
        # For now, generating synthetic data for demonstration

        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        dates = pd.date_range(start, end, freq=self.timeframe)
        n = len(dates)

        # Generate synthetic price data
        np.random.seed(42)
        base_price = 50000
        price_walk = np.cumsum(np.random.randn(n) * 100)
        close_prices = base_price + price_walk

        data = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.randn(n) * 50,
            'high': close_prices + abs(np.random.randn(n) * 100),
            'low': close_prices - abs(np.random.randn(n) * 100),
            'close': close_prices,
            'volume': abs(np.random.randn(n) * 1000000)
        })

        return data

    def train_dqn(
        self,
        data: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> DQNAgent:
        """
        Train DQN agent

        Args:
            data: Training data with indicators
            save_path: Path to save best model

        Returns:
            Trained DQN agent
        """
        # Create environment
        env = RLTradingEnvironment(
            data=data,
            initial_balance=self.initial_balance
        )

        # Get state size
        initial_state = env.reset()
        state_size = len(initial_state)

        # Create agent
        agent = DQNAgent(
            state_size=state_size,
            device=self.device
        )

        logger.info(f"Starting DQN training for {self.train_episodes} episodes")
        logger.info(f"State size: {state_size}")

        for episode in range(self.train_episodes):
            state = env.reset()
            episode_reward = 0
            episode_length = 0
            losses = []

            done = False
            while not done:
                # Select and perform action
                action = agent.select_action(state, training=True)
                next_state, reward, done, info = env.step(action)

                # Store experience
                agent.store_experience(state, action, reward, next_state, done)

                # Train
                loss = agent.train_step()
                if loss is not None:
                    losses.append(loss)

                episode_reward += reward
                episode_length += 1
                state = next_state

            # Record metrics
            self.episode_rewards.append(episode_reward)
            self.episode_profits.append(info['profit_pct'])
            self.episode_lengths.append(episode_length)
            if losses:
                self.training_losses.append(np.mean(losses))

            # Logging
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_profit = np.mean(self.episode_profits[-10:])
                avg_loss = np.mean(self.training_losses[-10:]) if self.training_losses else 0

                logger.info(
                    f"Episode {episode + 1}/{self.train_episodes} | "
                    f"Avg Reward: {avg_reward:.4f} | "
                    f"Avg Profit: {avg_profit:.2f}% | "
                    f"Avg Loss: {avg_loss:.4f} | "
                    f"Epsilon: {agent.epsilon:.4f}"
                )

            # Save best model
            if save_path and episode_reward > self.best_reward:
                self.best_reward = episode_reward
                agent.save(save_path)
                logger.info(f"New best model saved with reward: {episode_reward:.4f}")

        logger.info("DQN training completed")
        return agent

    def train_ppo(
        self,
        data: pd.DataFrame,
        save_path: Optional[str] = None,
        update_frequency: int = 2048  # Steps before update
    ) -> PPOAgent:
        """
        Train PPO agent

        Args:
            data: Training data with indicators
            save_path: Path to save best model
            update_frequency: Steps before policy update

        Returns:
            Trained PPO agent
        """
        # Create environment
        env = RLTradingEnvironment(
            data=data,
            initial_balance=self.initial_balance
        )

        # Get state size
        initial_state = env.reset()
        state_size = len(initial_state)

        # Create agent
        agent = PPOAgent(
            state_size=state_size,
            device=self.device
        )

        logger.info(f"Starting PPO training for {self.train_episodes} episodes")
        logger.info(f"State size: {state_size}")

        total_steps = 0

        for episode in range(self.train_episodes):
            state = env.reset()
            episode_reward = 0
            episode_length = 0

            done = False
            while not done:
                # Select and perform action
                action, log_prob, value = agent.select_action(state, training=True)
                next_state, reward, done, info = env.step(action)

                # Store reward
                agent.store_reward(reward, done)

                episode_reward += reward
                episode_length += 1
                total_steps += 1
                state = next_state

                # Update policy at fixed intervals
                if total_steps % update_frequency == 0:
                    loss = agent.train_step(epochs=4)
                    if loss is not None:
                        self.training_losses.append(loss)

            # Train at end of episode if not yet updated
            if episode_length > 0:
                loss = agent.train_step(epochs=4)
                if loss is not None:
                    self.training_losses.append(loss)

            # Record metrics
            self.episode_rewards.append(episode_reward)
            self.episode_profits.append(info['profit_pct'])
            self.episode_lengths.append(episode_length)

            # Logging
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_profit = np.mean(self.episode_profits[-10:])
                avg_loss = np.mean(self.training_losses[-10:]) if self.training_losses else 0

                logger.info(
                    f"Episode {episode + 1}/{self.train_episodes} | "
                    f"Avg Reward: {avg_reward:.4f} | "
                    f"Avg Profit: {avg_profit:.2f}% | "
                    f"Avg Loss: {avg_loss:.4f}"
                )

            # Save best model
            if save_path and info['profit_pct'] > self.best_profit:
                self.best_profit = info['profit_pct']
                agent.save(save_path)
                logger.info(f"New best model saved with profit: {info['profit_pct']:.2f}%")

        logger.info("PPO training completed")
        return agent

    def evaluate(
        self,
        agent,
        test_data: pd.DataFrame,
        n_episodes: int = 10
    ) -> Dict:
        """
        Evaluate trained agent

        Args:
            agent: Trained agent (DQN or PPO)
            test_data: Test data
            n_episodes: Number of evaluation episodes

        Returns:
            Evaluation metrics
        """
        logger.info(f"Evaluating agent for {n_episodes} episodes")

        env = RLTradingEnvironment(
            data=test_data,
            initial_balance=self.initial_balance
        )

        episode_profits = []
        episode_returns = []
        final_net_worths = []

        for episode in range(n_episodes):
            state = env.reset()
            episode_return = 0
            done = False

            while not done:
                # Select action (no exploration)
                if isinstance(agent, DQNAgent):
                    action = agent.select_action(state, training=False)
                else:  # PPO
                    action, _, _ = agent.select_action(state, training=False)

                next_state, reward, done, info = env.step(action)

                episode_return += reward
                state = next_state

            episode_profits.append(info['profit_pct'])
            episode_returns.append(episode_return)
            final_net_worths.append(info['net_worth'])

        results = {
            'avg_profit_pct': np.mean(episode_profits),
            'std_profit_pct': np.std(episode_profits),
            'max_profit_pct': np.max(episode_profits),
            'min_profit_pct': np.min(episode_profits),
            'avg_return': np.mean(episode_returns),
            'avg_final_net_worth': np.mean(final_net_worths),
            'win_rate': sum(1 for p in episode_profits if p > 0) / len(episode_profits) * 100
        }

        logger.info("Evaluation results:")
        for key, value in results.items():
            logger.info(f"  {key}: {value:.4f}")

        return results

    def plot_training_metrics(self, save_path: Optional[str] = None):
        """Plot training metrics"""
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(15, 10))

            # Episode rewards
            axes[0, 0].plot(self.episode_rewards)
            axes[0, 0].set_title('Episode Rewards')
            axes[0, 0].set_xlabel('Episode')
            axes[0, 0].set_ylabel('Reward')

            # Episode profits
            axes[0, 1].plot(self.episode_profits)
            axes[0, 1].set_title('Episode Profits (%)')
            axes[0, 1].set_xlabel('Episode')
            axes[0, 1].set_ylabel('Profit %')

            # Training loss
            if self.training_losses:
                axes[1, 0].plot(self.training_losses)
                axes[1, 0].set_title('Training Loss')
                axes[1, 0].set_xlabel('Step')
                axes[1, 0].set_ylabel('Loss')

            # Episode lengths
            axes[1, 1].plot(self.episode_lengths)
            axes[1, 1].set_title('Episode Lengths')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Steps')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                logger.info(f"Training plots saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            logger.warning("matplotlib not available, skipping plots")

    def get_training_summary(self) -> Dict:
        """Get summary of training"""
        return {
            'agent_type': self.agent_type,
            'total_episodes': len(self.episode_rewards),
            'avg_reward': np.mean(self.episode_rewards),
            'best_reward': self.best_reward,
            'avg_profit_pct': np.mean(self.episode_profits),
            'best_profit_pct': self.best_profit,
            'avg_episode_length': np.mean(self.episode_lengths),
            'final_epsilon': self.episode_rewards[-1] if self.episode_rewards else 0
        }


def main():
    """Example training script"""
    import argparse

    parser = argparse.ArgumentParser(description='Train RL trading agent')
    parser.add_argument('--agent', type=str, default='dqn', choices=['dqn', 'ppo'],
                        help='Agent type')
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                        help='Trading symbol')
    parser.add_argument('--episodes', type=int, default=1000,
                        help='Number of training episodes')
    parser.add_argument('--start-date', type=str, default='2023-01-01',
                        help='Training start date')
    parser.add_argument('--end-date', type=str, default='2023-12-31',
                        help='Training end date')
    parser.add_argument('--test-split', type=float, default=0.2,
                        help='Test split ratio')
    parser.add_argument('--save-dir', type=str, default='models/rl',
                        help='Directory to save models')

    args = parser.parse_args()

    # Create save directory
    os.makedirs(args.save_dir, exist_ok=True)

    # Initialize trainer
    trainer = RLTrainer(
        agent_type=args.agent,
        symbol=args.symbol,
        train_episodes=args.episodes
    )

    # Prepare data
    all_data = trainer.prepare_data(args.start_date, args.end_date)

    # Split train/test
    split_idx = int(len(all_data) * (1 - args.test_split))
    train_data = all_data.iloc[:split_idx]
    test_data = all_data.iloc[split_idx:]

    logger.info(f"Train samples: {len(train_data)}, Test samples: {len(test_data)}")

    # Train agent
    save_path = os.path.join(args.save_dir, f'{args.agent}_best_model.pth')

    if args.agent == 'dqn':
        agent = trainer.train_dqn(train_data, save_path=save_path)
    else:
        agent = trainer.train_ppo(train_data, save_path=save_path)

    # Evaluate
    eval_results = trainer.evaluate(agent, test_data, n_episodes=10)

    # Plot metrics
    plot_path = os.path.join(args.save_dir, f'{args.agent}_training_plots.png')
    trainer.plot_training_metrics(save_path=plot_path)

    # Print summary
    summary = trainer.get_training_summary()
    logger.info("\n=== Training Summary ===")
    for key, value in summary.items():
        logger.info(f"{key}: {value}")

    logger.info("\n=== Test Evaluation ===")
    for key, value in eval_results.items():
        logger.info(f"{key}: {value:.4f}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

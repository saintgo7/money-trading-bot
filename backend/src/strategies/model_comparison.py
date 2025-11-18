"""
Model Comparison and Selection Utility
Compare different AI models and automatically select the best performer
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Metrics for a single model"""
    model_name: str
    model_type: str

    # Performance metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Trading metrics
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0

    # Risk metrics
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk (95%)
    cvar_95: float = 0.0  # Conditional VaR

    # Efficiency metrics
    inference_time_ms: float = 0.0
    training_time_min: float = 0.0
    model_size_mb: float = 0.0

    # Metadata
    training_date: str = ""
    test_samples: int = 0
    parameters: Dict = field(default_factory=dict)


class SelectionCriteria(Enum):
    """Criteria for model selection"""
    SHARPE_RATIO = "sharpe_ratio"
    TOTAL_RETURN = "total_return"
    WIN_RATE = "win_rate"
    F1_SCORE = "f1_score"
    COMBINED = "combined"  # Weighted combination


class ModelComparator:
    """Compare and rank trading models"""

    def __init__(
        self,
        selection_criteria: SelectionCriteria = SelectionCriteria.COMBINED,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize comparator

        Args:
            selection_criteria: Primary criteria for selection
            weights: Custom weights for combined scoring
        """
        self.selection_criteria = selection_criteria

        # Default weights for combined scoring
        if weights is None:
            self.weights = {
                'sharpe_ratio': 0.25,
                'total_return': 0.20,
                'win_rate': 0.15,
                'f1_score': 0.15,
                'max_drawdown': 0.15,  # Negative weight
                'profit_factor': 0.10
            }
        else:
            self.weights = weights

        self.models = {}  # model_name -> ModelMetrics

    def add_model(self, metrics: ModelMetrics):
        """Add model metrics to comparison"""
        self.models[metrics.model_name] = metrics
        logger.info(f"Added model: {metrics.model_name}")

    def evaluate_backtest(
        self,
        model_name: str,
        predictions: pd.Series,
        actual_prices: pd.Series,
        trades: Optional[pd.DataFrame] = None
    ) -> ModelMetrics:
        """
        Evaluate model on backtest data

        Args:
            model_name: Name of the model
            predictions: Model predictions (0=sell, 1=hold, 2=buy)
            actual_prices: Actual price series
            trades: Optional DataFrame with executed trades

        Returns:
            ModelMetrics object
        """
        metrics = ModelMetrics(
            model_name=model_name,
            model_type="trading_model",
            training_date=datetime.now().strftime('%Y-%m-%d'),
            test_samples=len(predictions)
        )

        # Calculate returns
        returns = actual_prices.pct_change().dropna()

        # Create trading signals
        # Buy when predict=2, Sell when predict=0, Hold when predict=1
        positions = predictions.copy()
        positions[positions == 2] = 1  # Buy
        positions[positions == 0] = -1  # Sell
        positions[positions == 1] = 0  # Hold

        # Strategy returns
        strategy_returns = positions.shift(1) * returns
        strategy_returns = strategy_returns.dropna()

        # Performance metrics
        metrics.total_return = (1 + strategy_returns).prod() - 1
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(strategy_returns)
        metrics.max_drawdown = self._calculate_max_drawdown(strategy_returns)
        metrics.volatility = strategy_returns.std() * np.sqrt(252)

        # Risk metrics
        metrics.var_95 = np.percentile(strategy_returns, 5)
        metrics.cvar_95 = strategy_returns[strategy_returns <= metrics.var_95].mean()

        # Trading metrics from trades DataFrame
        if trades is not None:
            metrics.win_rate = self._calculate_win_rate(trades)
            metrics.profit_factor = self._calculate_profit_factor(trades)

        # Classification metrics
        if len(predictions) > 0:
            # Create binary target (up/down based on next return)
            target = (returns.shift(-1) > 0).astype(int)
            pred_binary = (predictions == 2).astype(int)  # Buy = 1, else = 0

            # Align indices
            common_idx = target.index.intersection(pred_binary.index)
            if len(common_idx) > 0:
                target_aligned = target.loc[common_idx]
                pred_aligned = pred_binary.loc[common_idx]

                metrics.accuracy = (target_aligned == pred_aligned).mean()
                metrics.precision = self._calculate_precision(pred_aligned, target_aligned)
                metrics.recall = self._calculate_recall(pred_aligned, target_aligned)
                metrics.f1_score = self._calculate_f1(metrics.precision, metrics.recall)

        self.add_model(metrics)
        return metrics

    def _calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252
        if len(returns) > 0 and returns.std() > 0:
            return np.sqrt(252) * excess_returns.mean() / returns.std()
        return 0.0

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """Calculate win rate from trades"""
        if 'pnl' in trades.columns and len(trades) > 0:
            winning_trades = (trades['pnl'] > 0).sum()
            return winning_trades / len(trades)
        return 0.0

    def _calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor"""
        if 'pnl' in trades.columns and len(trades) > 0:
            gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
            if gross_loss > 0:
                return gross_profit / gross_loss
        return 0.0

    def _calculate_precision(self, pred: pd.Series, target: pd.Series) -> float:
        """Calculate precision"""
        tp = ((pred == 1) & (target == 1)).sum()
        fp = ((pred == 1) & (target == 0)).sum()
        if tp + fp > 0:
            return tp / (tp + fp)
        return 0.0

    def _calculate_recall(self, pred: pd.Series, target: pd.Series) -> float:
        """Calculate recall"""
        tp = ((pred == 1) & (target == 1)).sum()
        fn = ((pred == 0) & (target == 1)).sum()
        if tp + fn > 0:
            return tp / (tp + fn)
        return 0.0

    def _calculate_f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall > 0:
            return 2 * precision * recall / (precision + recall)
        return 0.0

    def rank_models(self) -> List[Tuple[str, float, ModelMetrics]]:
        """
        Rank models by selection criteria

        Returns:
            List of (model_name, score, metrics) sorted by score
        """
        rankings = []

        for name, metrics in self.models.items():
            score = self._calculate_score(metrics)
            rankings.append((name, score, metrics))

        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)

        return rankings

    def _calculate_score(self, metrics: ModelMetrics) -> float:
        """Calculate overall score for a model"""
        if self.selection_criteria == SelectionCriteria.SHARPE_RATIO:
            return metrics.sharpe_ratio

        elif self.selection_criteria == SelectionCriteria.TOTAL_RETURN:
            return metrics.total_return

        elif self.selection_criteria == SelectionCriteria.WIN_RATE:
            return metrics.win_rate

        elif self.selection_criteria == SelectionCriteria.F1_SCORE:
            return metrics.f1_score

        elif self.selection_criteria == SelectionCriteria.COMBINED:
            # Normalize metrics to 0-1 range for fair combination
            normalized_scores = {
                'sharpe_ratio': self._normalize(metrics.sharpe_ratio, 0, 3),
                'total_return': self._normalize(metrics.total_return, -0.5, 0.5),
                'win_rate': metrics.win_rate,  # Already 0-1
                'f1_score': metrics.f1_score,  # Already 0-1
                'max_drawdown': 1 - self._normalize(abs(metrics.max_drawdown), 0, 0.5),
                'profit_factor': self._normalize(metrics.profit_factor, 0, 3)
            }

            # Weighted combination
            score = sum(
                normalized_scores.get(key, 0) * weight
                for key, weight in self.weights.items()
            )

            return score

        return 0.0

    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if max_val == min_val:
            return 0.5
        return np.clip((value - min_val) / (max_val - min_val), 0, 1)

    def get_best_model(self) -> Optional[Tuple[str, ModelMetrics]]:
        """
        Get the best performing model

        Returns:
            (model_name, metrics) or None if no models
        """
        if not self.models:
            return None

        rankings = self.rank_models()
        best_name, best_score, best_metrics = rankings[0]

        logger.info(f"Best model: {best_name} (score: {best_score:.4f})")

        return best_name, best_metrics

    def print_comparison(self):
        """Print detailed comparison table"""
        if not self.models:
            print("No models to compare")
            return

        rankings = self.rank_models()

        print("\n" + "=" * 120)
        print("MODEL COMPARISON REPORT")
        print("=" * 120)
        print(f"Selection Criteria: {self.selection_criteria.value}")
        print(f"Number of Models: {len(self.models)}")
        print("-" * 120)

        # Header
        print(f"{'Rank':<6}{'Model':<20}{'Score':<10}{'Return':<10}{'Sharpe':<10}{'Win Rate':<10}"
              f"{'Max DD':<10}{'F1':<10}")
        print("-" * 120)

        # Models
        for rank, (name, score, metrics) in enumerate(rankings, 1):
            print(f"{rank:<6}{name:<20}{score:<10.4f}{metrics.total_return:<10.2%}"
                  f"{metrics.sharpe_ratio:<10.2f}{metrics.win_rate:<10.2%}"
                  f"{metrics.max_drawdown:<10.2%}{metrics.f1_score:<10.4f}")

        print("=" * 120)

        # Detailed winner info
        best_name, _, best_metrics = rankings[0]
        print(f"\nBEST MODEL: {best_name}")
        print("-" * 60)
        print(f"Total Return:     {best_metrics.total_return:>10.2%}")
        print(f"Sharpe Ratio:     {best_metrics.sharpe_ratio:>10.2f}")
        print(f"Max Drawdown:     {best_metrics.max_drawdown:>10.2%}")
        print(f"Win Rate:         {best_metrics.win_rate:>10.2%}")
        print(f"Profit Factor:    {best_metrics.profit_factor:>10.2f}")
        print(f"F1 Score:         {best_metrics.f1_score:>10.4f}")
        print(f"Accuracy:         {best_metrics.accuracy:>10.2%}")
        print("-" * 60)

    def export_report(self, filepath: str):
        """Export comparison report to JSON"""
        rankings = self.rank_models()

        report = {
            'selection_criteria': self.selection_criteria.value,
            'weights': self.weights,
            'timestamp': datetime.now().isoformat(),
            'models': []
        }

        for rank, (name, score, metrics) in enumerate(rankings, 1):
            model_data = {
                'rank': rank,
                'name': name,
                'score': score,
                'metrics': {
                    'accuracy': metrics.accuracy,
                    'precision': metrics.precision,
                    'recall': metrics.recall,
                    'f1_score': metrics.f1_score,
                    'total_return': metrics.total_return,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'win_rate': metrics.win_rate,
                    'profit_factor': metrics.profit_factor,
                    'volatility': metrics.volatility,
                    'var_95': metrics.var_95,
                    'cvar_95': metrics.cvar_95
                }
            }
            report['models'].append(model_data)

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Comparison report exported to {filepath}")

    def visualize_comparison(self, save_path: Optional[str] = None):
        """Visualize model comparison"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches

            if not self.models:
                logger.warning("No models to visualize")
                return

            rankings = self.rank_models()

            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('Model Comparison Dashboard', fontsize=16, fontweight='bold')

            models = [name for name, _, _ in rankings]
            colors = plt.cm.viridis(np.linspace(0, 1, len(models)))

            # 1. Overall Scores
            scores = [score for _, score, _ in rankings]
            axes[0, 0].barh(models, scores, color=colors)
            axes[0, 0].set_xlabel('Score')
            axes[0, 0].set_title('Overall Scores')
            axes[0, 0].invert_yaxis()

            # 2. Total Returns
            returns = [m.total_return * 100 for _, _, m in rankings]
            axes[0, 1].barh(models, returns, color=colors)
            axes[0, 1].set_xlabel('Return (%)')
            axes[0, 1].set_title('Total Returns')
            axes[0, 1].invert_yaxis()

            # 3. Sharpe Ratios
            sharpes = [m.sharpe_ratio for _, _, m in rankings]
            axes[0, 2].barh(models, sharpes, color=colors)
            axes[0, 2].set_xlabel('Sharpe Ratio')
            axes[0, 2].set_title('Sharpe Ratios')
            axes[0, 2].invert_yaxis()

            # 4. Win Rates
            win_rates = [m.win_rate * 100 for _, _, m in rankings]
            axes[1, 0].barh(models, win_rates, color=colors)
            axes[1, 0].set_xlabel('Win Rate (%)')
            axes[1, 0].set_title('Win Rates')
            axes[1, 0].invert_yaxis()

            # 5. Max Drawdowns
            drawdowns = [m.max_drawdown * 100 for _, _, m in rankings]
            axes[1, 1].barh(models, drawdowns, color=colors)
            axes[1, 1].set_xlabel('Max Drawdown (%)')
            axes[1, 1].set_title('Maximum Drawdowns')
            axes[1, 1].invert_yaxis()

            # 6. F1 Scores
            f1_scores = [m.f1_score for _, _, m in rankings]
            axes[1, 2].barh(models, f1_scores, color=colors)
            axes[1, 2].set_xlabel('F1 Score')
            axes[1, 2].set_title('F1 Scores')
            axes[1, 2].invert_yaxis()

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Comparison visualization saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            logger.warning("matplotlib not available, skipping visualization")


def compare_models_example():
    """Example usage of ModelComparator"""

    # Create comparator
    comparator = ModelComparator(
        selection_criteria=SelectionCriteria.COMBINED
    )

    # Generate synthetic data for demonstration
    np.random.seed(42)
    n = 1000

    # Model 1: LSTM
    lstm_returns = pd.Series(np.random.randn(n) * 0.02 + 0.001)
    lstm_predictions = pd.Series(np.random.choice([0, 1, 2], n, p=[0.3, 0.4, 0.3]))
    lstm_prices = pd.Series(np.cumsum(lstm_returns) + 100)

    comparator.evaluate_backtest(
        model_name="LSTM",
        predictions=lstm_predictions,
        actual_prices=lstm_prices
    )

    # Model 2: DQN
    dqn_returns = pd.Series(np.random.randn(n) * 0.025 + 0.0015)
    dqn_predictions = pd.Series(np.random.choice([0, 1, 2], n, p=[0.25, 0.4, 0.35]))
    dqn_prices = pd.Series(np.cumsum(dqn_returns) + 100)

    comparator.evaluate_backtest(
        model_name="DQN",
        predictions=dqn_predictions,
        actual_prices=dqn_prices
    )

    # Model 3: Ensemble
    ensemble_returns = pd.Series(np.random.randn(n) * 0.018 + 0.0012)
    ensemble_predictions = pd.Series(np.random.choice([0, 1, 2], n, p=[0.2, 0.5, 0.3]))
    ensemble_prices = pd.Series(np.cumsum(ensemble_returns) + 100)

    comparator.evaluate_backtest(
        model_name="Ensemble",
        predictions=ensemble_predictions,
        actual_prices=ensemble_prices
    )

    # Print comparison
    comparator.print_comparison()

    # Get best model
    best_name, best_metrics = comparator.get_best_model()
    print(f"\nRecommended model: {best_name}")

    # Export report
    comparator.export_report("model_comparison_report.json")

    # Visualize
    comparator.visualize_comparison("model_comparison.png")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    compare_models_example()

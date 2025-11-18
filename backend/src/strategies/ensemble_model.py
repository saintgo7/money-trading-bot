"""
Ensemble Trading Model
Combines multiple AI models for robust trading decisions
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging
from dataclasses import dataclass

from .ai_model import LSTMTradingModel, TransformerTradingModel
from .rl_agent import DQNAgent, PPOAgent
from .indicators import calculate_all_indicators

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of models in ensemble"""
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    DQN = "dqn"
    PPO = "ppo"
    TECHNICAL = "technical"


@dataclass
class ModelPrediction:
    """Prediction from a single model"""
    model_type: ModelType
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-1
    price_prediction: Optional[float] = None
    metadata: Optional[Dict] = None


class VotingStrategy(Enum):
    """Voting strategies for ensemble"""
    MAJORITY = "majority"  # Simple majority vote
    WEIGHTED = "weighted"  # Weighted by confidence
    UNANIMOUS = "unanimous"  # All models must agree
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Minimum confidence required


class EnsembleModel:
    """
    Ensemble model combining multiple AI approaches

    Combines:
    - LSTM for time series prediction
    - Transformer for attention-based prediction
    - DQN for Q-learning based decisions
    - PPO for policy gradient decisions
    - Technical analysis rules
    """

    ACTIONS = ['HOLD', 'BUY', 'SELL']

    def __init__(
        self,
        state_size: int,
        voting_strategy: VotingStrategy = VotingStrategy.WEIGHTED,
        confidence_threshold: float = 0.6,
        model_weights: Optional[Dict[ModelType, float]] = None,
        device: str = None
    ):
        self.state_size = state_size
        self.voting_strategy = voting_strategy
        self.confidence_threshold = confidence_threshold

        # Device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Initialize models
        self.models = {}

        # LSTM model
        self.models[ModelType.LSTM] = LSTMTradingModel(
            input_size=state_size,
            hidden_size=128,
            num_layers=2
        )

        # Transformer model
        self.models[ModelType.TRANSFORMER] = TransformerTradingModel(
            input_size=state_size,
            d_model=128,
            nhead=8,
            num_layers=3
        )

        # DQN agent
        self.models[ModelType.DQN] = DQNAgent(
            state_size=state_size,
            device=self.device
        )

        # PPO agent
        self.models[ModelType.PPO] = PPOAgent(
            state_size=state_size,
            device=self.device
        )

        # Model weights (for weighted voting)
        if model_weights is None:
            # Default equal weights
            self.model_weights = {
                ModelType.LSTM: 0.25,
                ModelType.TRANSFORMER: 0.25,
                ModelType.DQN: 0.25,
                ModelType.PPO: 0.25
            }
        else:
            self.model_weights = model_weights

        # Performance tracking
        self.model_performance = {
            model_type: {'correct': 0, 'total': 0, 'avg_confidence': 0.0}
            for model_type in ModelType
        }

        logger.info(f"Ensemble model initialized with {len(self.models)} models")

    def predict(self, data: pd.DataFrame, training: bool = False) -> Dict:
        """
        Get ensemble prediction

        Args:
            data: DataFrame with OHLCV and indicators
            training: Whether in training mode

        Returns:
            Dictionary with prediction details
        """
        # Get predictions from all models
        predictions = self._get_model_predictions(data, training)

        # Aggregate predictions
        final_action, confidence, details = self._aggregate_predictions(predictions)

        return {
            'action': final_action,
            'confidence': confidence,
            'individual_predictions': predictions,
            'voting_details': details
        }

    def _get_model_predictions(
        self,
        data: pd.DataFrame,
        training: bool
    ) -> List[ModelPrediction]:
        """Get predictions from all models"""
        predictions = []

        # Prepare state
        state = self._prepare_state(data)

        # LSTM prediction
        lstm_pred = self._get_lstm_prediction(data, state)
        if lstm_pred:
            predictions.append(lstm_pred)

        # Transformer prediction
        transformer_pred = self._get_transformer_prediction(data, state)
        if transformer_pred:
            predictions.append(transformer_pred)

        # DQN prediction
        dqn_pred = self._get_dqn_prediction(state, training)
        if dqn_pred:
            predictions.append(dqn_pred)

        # PPO prediction
        ppo_pred = self._get_ppo_prediction(state, training)
        if ppo_pred:
            predictions.append(ppo_pred)

        # Technical analysis
        technical_pred = self._get_technical_prediction(data)
        if technical_pred:
            predictions.append(technical_pred)

        return predictions

    def _get_lstm_prediction(
        self,
        data: pd.DataFrame,
        state: np.ndarray
    ) -> Optional[ModelPrediction]:
        """Get LSTM model prediction"""
        try:
            lstm_model = self.models[ModelType.LSTM]
            result = lstm_model.predict(data)

            # Determine action based on predicted price change
            if result['predicted_change'] > 0.01:  # >1% increase predicted
                action = 'BUY'
                confidence = min(abs(result['predicted_change']) * 10, 1.0)
            elif result['predicted_change'] < -0.01:  # >1% decrease predicted
                action = 'SELL'
                confidence = min(abs(result['predicted_change']) * 10, 1.0)
            else:
                action = 'HOLD'
                confidence = 0.5

            return ModelPrediction(
                model_type=ModelType.LSTM,
                action=action,
                confidence=confidence,
                price_prediction=result.get('predicted_price'),
                metadata={'change': result['predicted_change']}
            )
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return None

    def _get_transformer_prediction(
        self,
        data: pd.DataFrame,
        state: np.ndarray
    ) -> Optional[ModelPrediction]:
        """Get Transformer model prediction"""
        try:
            transformer_model = self.models[ModelType.TRANSFORMER]
            result = transformer_model.predict(data)

            # Similar logic to LSTM
            if result['predicted_change'] > 0.01:
                action = 'BUY'
                confidence = min(abs(result['predicted_change']) * 10, 1.0)
            elif result['predicted_change'] < -0.01:
                action = 'SELL'
                confidence = min(abs(result['predicted_change']) * 10, 1.0)
            else:
                action = 'HOLD'
                confidence = 0.5

            return ModelPrediction(
                model_type=ModelType.TRANSFORMER,
                action=action,
                confidence=confidence,
                price_prediction=result.get('predicted_price'),
                metadata={'change': result['predicted_change']}
            )
        except Exception as e:
            logger.error(f"Transformer prediction error: {e}")
            return None

    def _get_dqn_prediction(
        self,
        state: np.ndarray,
        training: bool
    ) -> Optional[ModelPrediction]:
        """Get DQN agent prediction"""
        try:
            dqn_agent = self.models[ModelType.DQN]
            action_idx = dqn_agent.select_action(state, training=training)
            action = self.ACTIONS[action_idx]

            # Get Q-values for confidence
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = dqn_agent.policy_net(state_tensor)
                max_q = q_values.max().item()
                min_q = q_values.min().item()

                # Normalize confidence
                if max_q != min_q:
                    confidence = (q_values[0][action_idx].item() - min_q) / (max_q - min_q)
                else:
                    confidence = 0.5

            return ModelPrediction(
                model_type=ModelType.DQN,
                action=action,
                confidence=confidence,
                metadata={'q_values': q_values[0].cpu().numpy().tolist()}
            )
        except Exception as e:
            logger.error(f"DQN prediction error: {e}")
            return None

    def _get_ppo_prediction(
        self,
        state: np.ndarray,
        training: bool
    ) -> Optional[ModelPrediction]:
        """Get PPO agent prediction"""
        try:
            ppo_agent = self.models[ModelType.PPO]
            action_idx, log_prob, value = ppo_agent.select_action(state, training=training)
            action = self.ACTIONS[action_idx]

            # Use action probability as confidence
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                action_probs, _ = ppo_agent.network(state_tensor)
                confidence = action_probs[0][action_idx].item()

            return ModelPrediction(
                model_type=ModelType.PPO,
                action=action,
                confidence=confidence,
                metadata={
                    'value': value,
                    'action_probs': action_probs[0].cpu().numpy().tolist()
                }
            )
        except Exception as e:
            logger.error(f"PPO prediction error: {e}")
            return None

    def _get_technical_prediction(self, data: pd.DataFrame) -> Optional[ModelPrediction]:
        """Get technical analysis based prediction"""
        try:
            if len(data) < 2:
                return None

            latest = data.iloc[-1]
            prev = data.iloc[-2]

            # Simple technical rules
            signals = []
            confidences = []

            # RSI
            if 'rsi' in latest:
                if latest['rsi'] < 30:
                    signals.append('BUY')
                    confidences.append(0.7)
                elif latest['rsi'] > 70:
                    signals.append('SELL')
                    confidences.append(0.7)

            # MACD
            if 'macd' in latest and 'macd_signal' in latest:
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals.append('BUY')
                    confidences.append(0.6)
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals.append('SELL')
                    confidences.append(0.6)

            # Bollinger Bands
            if 'bb_lower' in latest and 'bb_upper' in latest:
                if latest['close'] < latest['bb_lower']:
                    signals.append('BUY')
                    confidences.append(0.5)
                elif latest['close'] > latest['bb_upper']:
                    signals.append('SELL')
                    confidences.append(0.5)

            # Aggregate technical signals
            if not signals:
                action = 'HOLD'
                confidence = 0.5
            else:
                # Most common signal
                action = max(set(signals), key=signals.count)
                confidence = np.mean(confidences)

            return ModelPrediction(
                model_type=ModelType.TECHNICAL,
                action=action,
                confidence=confidence,
                metadata={'signals': signals, 'confidences': confidences}
            )
        except Exception as e:
            logger.error(f"Technical prediction error: {e}")
            return None

    def _aggregate_predictions(
        self,
        predictions: List[ModelPrediction]
    ) -> Tuple[str, float, Dict]:
        """
        Aggregate predictions using voting strategy

        Returns:
            final_action, confidence, details
        """
        if not predictions:
            return 'HOLD', 0.0, {'error': 'No predictions available'}

        if self.voting_strategy == VotingStrategy.MAJORITY:
            return self._majority_vote(predictions)
        elif self.voting_strategy == VotingStrategy.WEIGHTED:
            return self._weighted_vote(predictions)
        elif self.voting_strategy == VotingStrategy.UNANIMOUS:
            return self._unanimous_vote(predictions)
        elif self.voting_strategy == VotingStrategy.CONFIDENCE_THRESHOLD:
            return self._confidence_threshold_vote(predictions)
        else:
            return self._weighted_vote(predictions)

    def _majority_vote(
        self,
        predictions: List[ModelPrediction]
    ) -> Tuple[str, float, Dict]:
        """Simple majority voting"""
        votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        confidences = {'BUY': [], 'SELL': [], 'HOLD': []}

        for pred in predictions:
            votes[pred.action] += 1
            confidences[pred.action].append(pred.confidence)

        # Get majority action
        final_action = max(votes, key=votes.get)

        # Average confidence for winning action
        if confidences[final_action]:
            confidence = np.mean(confidences[final_action])
        else:
            confidence = 0.5

        return final_action, confidence, {
            'votes': votes,
            'voting_strategy': 'majority'
        }

    def _weighted_vote(
        self,
        predictions: List[ModelPrediction]
    ) -> Tuple[str, float, Dict]:
        """Weighted voting by model weights and confidence"""
        scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}

        for pred in predictions:
            weight = self.model_weights.get(pred.model_type, 0.2)
            scores[pred.action] += weight * pred.confidence

        # Normalize scores
        total_score = sum(scores.values())
        if total_score > 0:
            for action in scores:
                scores[action] /= total_score

        # Get action with highest score
        final_action = max(scores, key=scores.get)
        confidence = scores[final_action]

        return final_action, confidence, {
            'scores': scores,
            'voting_strategy': 'weighted'
        }

    def _unanimous_vote(
        self,
        predictions: List[ModelPrediction]
    ) -> Tuple[str, float, Dict]:
        """Unanimous voting - all models must agree"""
        actions = set(pred.action for pred in predictions)

        if len(actions) == 1:
            # All agree
            final_action = actions.pop()
            confidence = np.mean([pred.confidence for pred in predictions])
        else:
            # Disagreement - default to HOLD
            final_action = 'HOLD'
            confidence = 0.3

        return final_action, confidence, {
            'unanimous': len(actions) == 1,
            'voting_strategy': 'unanimous'
        }

    def _confidence_threshold_vote(
        self,
        predictions: List[ModelPrediction]
    ) -> Tuple[str, float, Dict]:
        """Only act if confidence exceeds threshold"""
        # Use weighted voting
        final_action, confidence, details = self._weighted_vote(predictions)

        # Override with HOLD if below threshold
        if confidence < self.confidence_threshold:
            final_action = 'HOLD'

        details['confidence_threshold'] = self.confidence_threshold
        details['voting_strategy'] = 'confidence_threshold'

        return final_action, confidence, details

    def _prepare_state(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare state vector from data"""
        if len(data) == 0:
            return np.zeros(self.state_size)

        latest = data.iloc[-1]

        # Select features (adjust based on your indicators)
        feature_columns = [
            'close', 'volume', 'rsi', 'macd', 'macd_signal',
            'bb_upper', 'bb_middle', 'bb_lower',
            'sma_20', 'ema_20', 'atr', 'adx'
        ]

        state = []
        for col in feature_columns:
            if col in latest:
                state.append(latest[col])
            else:
                state.append(0.0)

        # Pad or truncate to state_size
        state = np.array(state)
        if len(state) < self.state_size:
            state = np.pad(state, (0, self.state_size - len(state)))
        elif len(state) > self.state_size:
            state = state[:self.state_size]

        return state

    def update_model_weights(self, performance_data: Dict[ModelType, Dict]):
        """
        Update model weights based on recent performance

        Args:
            performance_data: Dict with accuracy/performance metrics per model
        """
        total_performance = sum(data.get('accuracy', 0.5) for data in performance_data.values())

        if total_performance > 0:
            for model_type, data in performance_data.items():
                accuracy = data.get('accuracy', 0.5)
                self.model_weights[model_type] = accuracy / total_performance

        logger.info(f"Updated model weights: {self.model_weights}")

    def save(self, base_path: str):
        """Save all ensemble models"""
        import os
        os.makedirs(base_path, exist_ok=True)

        # Save each model
        for model_type, model in self.models.items():
            filepath = os.path.join(base_path, f"{model_type.value}_model.pth")
            if hasattr(model, 'save'):
                model.save(filepath)

        # Save weights
        import json
        weights_path = os.path.join(base_path, "ensemble_weights.json")
        with open(weights_path, 'w') as f:
            json.dump({k.value: v for k, v in self.model_weights.items()}, f)

        logger.info(f"Ensemble model saved to {base_path}")

    def load(self, base_path: str):
        """Load all ensemble models"""
        import os
        import json

        # Load each model
        for model_type, model in self.models.items():
            filepath = os.path.join(base_path, f"{model_type.value}_model.pth")
            if os.path.exists(filepath) and hasattr(model, 'load'):
                model.load(filepath)

        # Load weights
        weights_path = os.path.join(base_path, "ensemble_weights.json")
        if os.path.exists(weights_path):
            with open(weights_path, 'r') as f:
                weights_data = json.load(f)
                self.model_weights = {
                    ModelType(k): v for k, v in weights_data.items()
                }

        logger.info(f"Ensemble model loaded from {base_path}")

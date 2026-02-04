"""AI package for environmental prediction models."""

from .environmental_ai import (
    EnvironmentalAISystem,
    PM25PredictionModel,
    EnvironmentalHealthClassifier,
    EnvironmentalDataset,
    ModelMetrics
)
from .spike_predictor import PollutionSpikePredictor, SpikePrediction

__all__ = [
    'EnvironmentalAISystem',
    'PM25PredictionModel',
    'EnvironmentalHealthClassifier',
    'EnvironmentalDataset',
    'ModelMetrics',
    'PollutionSpikePredictor',
    'SpikePrediction'
]

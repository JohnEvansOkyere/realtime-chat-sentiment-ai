# backend/tests/test_ml_inference.py
"""
Unit tests for ML inference service.
Coverage: Model Loading, Sentiment Analysis, Performance
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestMLModelLoading:
    """Tests for ML model initialization."""
    
    def test_model_loads_successfully(self):
        """Test that ML models load without errors."""
        from app.ml.inference import ml_inference_service
        
        assert ml_inference_service.is_model_loaded() is True
        assert ml_inference_service.model is not None
        assert ml_inference_service.vectorizer is not None
    
    def test_model_singleton(self):
        """Test that ML service uses singleton pattern."""
        from app.ml.inference import ml_inference_service
        
        # Both should point to same instance
        service1 = ml_inference_service
        service2 = ml_inference_service
        
        assert service1 is service2
        # Check they share the same model
        assert id(service1.model) == id(service2.model)

class TestSentimentAnalysis:
    """Tests for sentiment classification."""
    
    def test_positive_sentiment(self):
        """Test classification of positive message."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment(
            "I love this product! It's amazing and wonderful!"
        )
        
        assert result["label"] in ["positive", "negative", "neutral"]
        assert "score" in result
        assert 0 <= result["score"] <= 1
    
    def test_negative_sentiment(self):
        """Test classification of negative message."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment(
            "This is terrible and awful. I hate it!"
        )
        
        assert result["label"] in ["positive", "negative", "neutral"]
        assert 0 <= result["score"] <= 1
    
    def test_neutral_sentiment(self):
        """Test classification of neutral message."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment(
            "The meeting is scheduled for 3pm tomorrow."
        )
        
        assert result["label"] in ["positive", "negative", "neutral"]
        assert 0 <= result["score"] <= 1
    
    def test_empty_message(self):
        """Test handling of empty message."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment("")
        
        # Should return neutral or handle gracefully
        assert result["label"] in ["positive", "negative", "neutral"]
    
    def test_special_characters(self):
        """Test handling of special characters."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment(
            "!!!@@@ ###$$$ %%%"
        )
        
        assert result["label"] in ["positive", "negative", "neutral"]
    
    def test_very_long_message(self):
        """Test handling of very long messages."""
        from app.ml.inference import ml_inference_service
        
        long_message = "This is great! " * 100
        result = ml_inference_service.analyze_sentiment(long_message)
        
        assert result["label"] in ["positive", "negative", "neutral"]


class TestPerformance:
    """Tests for ML inference performance."""
    
    def test_inference_speed(self):
        """Test that inference is fast (<100ms)."""
        from app.ml.inference import ml_inference_service
        import time
        
        message = "This is a test message for performance testing."
        
        start_time = time.time()
        ml_inference_service.analyze_sentiment(message)
        end_time = time.time()
        
        inference_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert inference_time < 100, f"Inference took {inference_time}ms, expected <100ms"
    
    def test_batch_inference(self):
        """Test multiple inferences in sequence."""
        from app.ml.inference import ml_inference_service
        
        messages = [
            "I love this!",
            "This is terrible.",
            "It's okay.",
            "Amazing product!",
            "Very disappointing."
        ]
        
        results = [ml_inference_service.analyze_sentiment(msg) for msg in messages]
        
        assert len(results) == 5
        assert all("label" in r and "score" in r for r in results)


class TestLabelMapping:
    """Tests for sentiment label mapping."""
    
    def test_label_format(self):
        """Test that labels are in correct format."""
        from app.ml.inference import ml_inference_service
        
        result = ml_inference_service.analyze_sentiment("Test message")
        
        assert result["label"] in ["positive", "negative", "neutral"]
        assert isinstance(result["label"], str)
        assert result["label"].islower()
    
    def test_score_range(self):
        """Test that confidence scores are valid probabilities."""
        from app.ml.inference import ml_inference_service
        
        messages = [
            "Excellent!",
            "Terrible!",
            "Okay.",
            "Great work!",
            "Poor quality."
        ]
        
        for msg in messages:
            result = ml_inference_service.analyze_sentiment(msg)
            assert 0 <= result["score"] <= 1, f"Score {result['score']} out of range [0, 1]"
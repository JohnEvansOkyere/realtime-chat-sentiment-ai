# backend/app/ml/inference.py
"""
ML Inference service using existing YouTube sentiment model.
Time Complexity: O(1) per prediction
Space Complexity: O(1) - models loaded in memory
"""
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MLInferenceService:
    """Handles ML inference using existing LightGBM sentiment model."""
    
    def __init__(self):
        """Load pre-trained models from disk."""
        self.models_dir = Path("/app/ml/models")
        self.model = None
        self.vectorizer = None
        self._load_models()
    
    def _load_models(self):
        """Load LightGBM model and TF-IDF vectorizer."""
        try:
            model_path = self.models_dir / "lgbm_model.pkl"
            vectorizer_path = self.models_dir / "tfidf_vectorizer.pkl"
            
            if model_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                logger.info("✓ Sentiment model loaded successfully")
            else:
                logger.error(f"Model files not found in {self.models_dir}")
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using LightGBM model.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment label and confidence
            
        Business Value: Real-time emotion detection in conversations
        """
        if not self.model or not self.vectorizer:
            return {"label": "neutral", "score": 0.0}
        
        try:
            # Vectorize text
            text_vector = self.vectorizer.transform([text])
            
            # Predict
            prediction = self.model.predict(text_vector)[0]
            
            # Get probability scores if available
            try:
                probabilities = self.model.predict_proba(text_vector)[0]
                confidence = float(max(probabilities))
            except:
                confidence = 1.0
            
            # Map numeric labels to sentiment strings
            # Adjust based on your model's output
            label_map = {
                0: "negative",
                1: "neutral", 
                2: "positive"
            }
            
            sentiment = label_map.get(prediction, "neutral")
            
            return {
                "label": sentiment,
                "score": confidence
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"label": "neutral", "score": 0.0}
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.vectorizer is not None


# Singleton instance
ml_inference_service = MLInferenceService()
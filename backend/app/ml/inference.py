# backend/app/ml/inference.py
"""
ML Inference service using existing YouTube sentiment model.
"""
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class MLInferenceService:
    """Handles ML inference using existing LightGBM sentiment model."""
    
    def __init__(self):
        """Load pre-trained models from disk."""
        # Use relative path for local dev, absolute for Docker
        if os.path.exists("/app/ml/models"):
            self.models_dir = Path("/app/ml/models")  # Docker
        else:
            self.models_dir = Path(__file__).parent / "models"  # Local
        
        self.model = None
        self.vectorizer = None
        self._load_models()
    
    def _load_models(self):
        """Load LightGBM model and TF-IDF vectorizer."""
        try:
            model_path = self.models_dir / "lgbm_model.pkl"
            vectorizer_path = self.models_dir / "tfidf_vectorizer.pkl"
            
            print(f"Looking for models in: {self.models_dir}")
            print(f"Model exists: {model_path.exists()}")
            print(f"Vectorizer exists: {vectorizer_path.exists()}")
            
            if model_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                logger.info("✓ Sentiment model loaded successfully")
                
                # DEBUG: Check model attributes
                print(f"Model type: {type(self.model)}")
                if hasattr(self.model, 'classes_'):
                    print(f"Model classes: {self.model.classes_}")
                    print(f"Classes_ type: {type(self.model.classes_[0])}") 
            else:
                logger.error(f"Model files not found in {self.models_dir}")
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            import traceback
            traceback.print_exc()
    
    # backend/app/ml/inference.py
# Update the analyze_sentiment method:

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using LightGBM model.
        """
        if not self.model or not self.vectorizer:
            print("WARNING: Model not loaded, returning neutral")
            return {"label": "neutral", "score": 0.0}
        
        try:
            # Vectorize text
            text_vector = self.vectorizer.transform([text])
            
            # Predict
            prediction = self.model.predict(text_vector)[0]
            
            # Get probability scores
            try:
                probabilities = self.model.predict_proba(text_vector)[0]
                confidence = float(max(probabilities))
            except:
                confidence = 1.0
            
            # Map your model's classes: [-1, 0, 1] → [negative, neutral, positive]
            label_map = {
                -1: "negative",
                0: "neutral",
                1: "positive"
            }
            
            sentiment = label_map.get(int(prediction), "neutral")
            
            print(f"✓ Sentiment: {sentiment} ({confidence:.2%}) for: '{text[:50]}'")
            
            return {
                "label": sentiment,
                "score": confidence
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"label": "neutral", "score": 0.0}
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.vectorizer is not None


# Singleton instance
ml_inference_service = MLInferenceService()
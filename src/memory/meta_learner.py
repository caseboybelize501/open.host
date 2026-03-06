from typing import Dict, List, Optional
import os


class MetaLearner:
    """
    Meta-learning index that predicts cycles-to-stable based on historical data.
    
    Uses sklearn to learn patterns:
    - Which project types reach stable fastest
    - Which platforms are easiest to deploy to
    - Which approaches (naive vs memory-guided) work best
    
    Model: Linear Regression (can be upgraded to RandomForest for more data)
    """
    
    def __init__(self):
        self.training_data: List[Dict] = []
        self.model = None
        self.model_trained = False
        self.recent_predictions: List[Dict] = []
        
        # Try to import sklearn
        self._sklearn_available = self._check_sklearn()
        
        if self._sklearn_available:
            self._initialize_model()
    
    def _check_sklearn(self) -> bool:
        """Check if sklearn is available."""
        try:
            from sklearn.linear_model import LinearRegression
            return True
        except ImportError:
            print("sklearn not available. Using simple averaging for predictions.")
            return False
    
    def _initialize_model(self):
        """Initialize sklearn model."""
        try:
            from sklearn.linear_model import LinearRegression
            self.model = LinearRegression()
        except Exception as e:
            print(f"Failed to initialize model: {e}")
            self._sklearn_available = False
    
    def update_meta_learning(self, project_type: str, approach: str, 
                            cycles_to_stable: int, 
                            platform: Optional[str] = None):
        """
        Update meta-learning with new deployment outcome.
        
        Args:
            project_type: Type of project (react, vue, python, etc.)
            approach: Approach used (naive, memory_guided, platform_tuned)
            cycles_to_stable: Number of cycles to reach STABLE status
            platform: Optional platform name
        """
        # Store training data
        self.training_data.append({
            "project_type": project_type,
            "approach": approach,
            "platform": platform,
            "cycles": cycles_to_stable,
            "timestamp": self._get_timestamp()
        })
        
        # Retrain model if we have enough data
        if len(self.training_data) >= 5:
            self._retrain_model()
    
    def _retrain_model(self):
        """Retrain model with current data."""
        if not self._sklearn_available or len(self.training_data) < 5:
            return
        
        try:
            X = []
            y = []
            
            for data in self.training_data:
                # Feature engineering
                features = self._encode_features(
                    data["project_type"],
                    data["approach"],
                    data.get("platform")
                )
                X.append(features)
                y.append(data["cycles"])
            
            if len(X) >= 5:
                self.model.fit(X, y)
                self.model_trained = True
        except Exception as e:
            print(f"Failed to retrain model: {e}")
    
    def _encode_features(self, project_type: str, approach: str, 
                        platform: Optional[str]) -> List[float]:
        """Encode categorical features as numeric."""
        # Simple hash-based encoding (could be improved with proper embeddings)
        features = [
            hash(project_type) % 100 / 100.0,
            hash(approach) % 100 / 100.0,
        ]
        
        if platform:
            features.append(hash(platform) % 100 / 100.0)
        else:
            features.append(0.0)
        
        # Approach bonus (memory-guided should be better)
        approach_bonus = 1.0 if approach == "memory_guided" else 0.5
        features.append(approach_bonus)
        
        return features
    
    def predict_cycles(self, project_type: str, approach: str,
                      platform: Optional[str] = None) -> int:
        """
        Predict cycles-to-stable for given parameters.
        
        Returns:
            Predicted number of cycles to reach STABLE
        """
        # Store prediction for history
        prediction = {
            "project_type": project_type,
            "approach": approach,
            "platform": platform,
            "predicted_cycles": 0
        }
        
        # If model not trained, use simple averaging
        if not self.model_trained or not self._sklearn_available:
            predicted = self._predict_simple(project_type, approach)
        else:
            # Use trained model
            try:
                features = self._encode_features(project_type, approach, platform)
                predicted = int(self.model.predict([features])[0])
                predicted = max(1, min(predicted, 10))  # Clamp to reasonable range
            except Exception:
                predicted = self._predict_simple(project_type, approach)
        
        prediction["predicted_cycles"] = predicted
        self.recent_predictions.append(prediction)
        
        # Keep only recent predictions
        if len(self.recent_predictions) > 20:
            self.recent_predictions = self.recent_predictions[-20:]
        
        return predicted
    
    def _predict_simple(self, project_type: str, approach: str) -> int:
        """Simple prediction using averaging when model not available."""
        # Filter data for similar projects
        relevant = [
            d for d in self.training_data
            if d["project_type"] == project_type and d["approach"] == approach
        ]
        
        if relevant:
            # Average of similar projects
            avg = sum(d["cycles"] for d in relevant) / len(relevant)
            return int(round(avg))
        
        # Default based on approach
        if approach == "memory_guided":
            return 2  # Memory-guided should be faster
        elif approach == "platform_tuned":
            return 3
        else:
            return 4  # Naive approach takes longer
    
    def get_training_summary(self) -> Dict:
        """Get summary of training data."""
        if not self.training_data:
            return {
                "total_samples": 0,
                "project_types": [],
                "approaches": [],
                "avg_cycles": 0
            }
        
        project_types = list(set(d["project_type"] for d in self.training_data))
        approaches = list(set(d["approach"] for d in self.training_data))
        avg_cycles = sum(d["cycles"] for d in self.training_data) / len(self.training_data)
        
        return {
            "total_samples": len(self.training_data),
            "project_types": project_types,
            "approaches": approaches,
            "avg_cycles": round(avg_cycles, 2),
            "model_trained": self.model_trained
        }
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global instance
meta_learner = MetaLearner()


def update_meta_learning(project_type: str, approach: str, cycles_to_stable: int,
                        platform: Optional[str] = None):
    """Convenience function to update meta-learning."""
    meta_learner.update_meta_learning(project_type, approach, cycles_to_stable, platform)


def predict_cycles(project_type: str, approach: str, 
                  platform: Optional[str] = None) -> int:
    """Predict cycles."""
    return meta_learner.predict_cycles(project_type, approach, platform)


def get_training_summary() -> Dict:
    """Get training summary."""
    return meta_learner.get_training_summary()

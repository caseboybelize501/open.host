from sklearn.linear_model import LinearRegression
import numpy as np

class MetaLearner:
    def __init__(self):
        self.model = LinearRegression()
        self.training_data = []
        
    def update_meta_learning(self, project_type: str, approach: str, cycles_to_stable: int):
        # Store training data
        self.training_data.append({
            "project_type": project_type,
            "approach": approach,
            "cycles": cycles_to_stable
        })
        
        # Retrain model if we have enough data
        if len(self.training_data) >= 10:
            self._retrain_model()
    
    def _retrain_model(self):
        X = []
        y = []
        
        for data in self.training_data:
            # Simple feature engineering
            features = [hash(data["project_type"]) % 100, hash(data["approach"]) % 100]
            X.append(features)
            y.append(data["cycles"])
        
        if len(X) > 0:
            self.model.fit(X, y)
    
    def predict_cycles(self, project_type: str, approach: str) -> int:
        features = [hash(project_type) % 100, hash(approach) % 100]
        return int(self.model.predict([features])[0])

# Global instance
meta_learner = MetaLearner()

def update_meta_learning(project_type: str, approach: str, cycles_to_stable: int):
    meta_learner.update_meta_learning(project_type, approach, cycles_to_stable)

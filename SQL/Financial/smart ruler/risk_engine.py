from decimal import Decimal
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class RiskEngine:
    def __init__(self):
        self.model = RandomForestClassifier(random_state=42)
        self._train_mock_model()

    def _train_mock_model(self) -> None:
        features = np.array([
            [15, 1500.00, 1],
            [45, 2800.00, 2],
            [75, 5000.00, 3],
            [5, 950.00, 0],
            [32, 4300.00, 2],
            [3, 500.00, 0],
            [90, 10000.00, 5]
        ])
        labels = np.array([1, 0, 0, 1, 0, 1, 0])
        self.model.fit(features, labels)

    def predict_probability(self, days_overdue: int, amount: Decimal, historical_delays: int) -> float:
        input_data = np.array([[days_overdue, float(amount), historical_delays]])
        probabilities = self.model.predict_proba(input_data)
        return float(probabilities[0][1])
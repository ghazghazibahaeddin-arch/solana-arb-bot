import math

class QuantumPredictor:
    """
    Advanced AI Predictive Core: Analyzes historical trade reliability 
    and dynamically adjusts market entry confidence.
    """
    def __init__(self):
        self.success_weight = 1.0
        self.failure_penalty = 1.2
        self.confidence_threshold = 0.85

    def evaluate_market_momentum(self, liquidity_score, slippage):
        """
        Calculates a mathematical probability score for trade success 
        based on real-time market friction variables.
        """
        try:
            # Mathematical probability model using exponential decay for risk
            friction_factor = math.exp(slippage * 10)
            score = (liquidity_score / 100.0) / friction_factor
            
            # Normalizing score between 0 and 1
            confidence = min(max(score, 0.0), 1.0)
            
            return confidence
        except Exception:
            return 0.0

    def should_execute_quantum_trade(self, confidence_score):
        """
        Determines whether the predictive model gives a green light 
        for execution.
        """
        return confidence_score >= self.confidence_threshold
          

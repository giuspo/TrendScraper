from dataclasses import dataclass

@dataclass
class ScoreWeights:
    trend: float = 0.25
    competitor: float = 0.25
    margin: float = 0.25
    size: float = 0.15
    compliance: float = 0.10

class ScoringEngine:
    @staticmethod
    def calculate_opportunity_score(
        trend_score_0_100: float,
        comp_score_0_100: float,
        margin_percent: float,
        weight_g: float,
        compliance_score_0_100: float
    ) -> float:
        weights = ScoreWeights()
        
        # Normalizzazione margine (assumendo 30% come target 100%)
        margin_score = min((margin_percent / 30.0) * 100, 100.0) if margin_percent > 0 else 0
        
        # Normalizzazione peso (più è leggero meglio è)
        # Es: 100g = 100 punti, 800g = 0 punti
        if weight_g <= 100:
            size_score = 100.0
        elif weight_g >= 800:
            size_score = 0.0
        else:
            size_score = 100.0 - ((weight_g - 100) / 700.0) * 100.0
            
        final_score = (
            (trend_score_0_100 * weights.trend) +
            (comp_score_0_100 * weights.competitor) +
            (margin_score * weights.margin) +
            (size_score * weights.size) +
            (compliance_score_0_100 * weights.compliance)
        )
        
        return round(final_score, 2)

    @staticmethod
    def get_badge_color(score: float) -> str:
        if score >= 80:
            return "Verde"
        elif score >= 60:
            return "Giallo"
        else:
            return "Rosso"

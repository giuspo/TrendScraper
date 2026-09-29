import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Tuple

class RuleProfile(BaseModel):
    max_weight_grams: float
    max_dimensions_cm: List[float]
    allow_220v_ac: bool
    max_battery_mah: float
    min_net_margin_percent: float
    banned_keywords: List[str]

class RulesEngine:
    def __init__(self, config_path: str = "config/rules.yaml", active_profile: str = "default"):
        self.config_path = Path(config_path)
        self.active_profile_name = active_profile
        self.profile = self._load_profile(active_profile)

    def _load_profile(self, profile_name: str) -> RuleProfile:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Rules configuration not found at {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        profiles = data.get("profiles", {})
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found in {self.config_path}")
            
        return RuleProfile(**profiles[profile_name])

    def check_compliance(self, 
                         weight_g: float, 
                         dimensions_cm: List[float], 
                         is_220v: bool, 
                         battery_mah: float, 
                         title_or_desc: str) -> Tuple[bool, str]:
        """
        Controlla se un prodotto supera i criteri di esclusione dinamici.
        Ritorna (True, "") se conforme, (False, "Motivo") se scartato.
        """
        # 1. Controllo Peso
        if weight_g > self.profile.max_weight_grams:
            return False, f"Peso eccedente: {weight_g}g > {self.profile.max_weight_grams}g"
            
        # 2. Controllo Dimensioni (Verifica volume o singoli lati)
        # Semplificazione: controllo sul lato maggiore
        if any(d > max_d for d, max_d in zip(sorted(dimensions_cm, reverse=True), sorted(self.profile.max_dimensions_cm, reverse=True))):
            return False, f"Dimensioni eccedenti i limiti pacco standard"
            
        # 3. Controllo 220V
        if is_220v and not self.profile.allow_220v_ac:
            return False, "Alimentazione a 220V AC non consentita"
            
        # 4. Controllo Batteria
        if battery_mah > self.profile.max_battery_mah > 0:
            return False, f"Batteria eccedente: {battery_mah}mAh > {self.profile.max_battery_mah}mAh"
        elif battery_mah > 0 and self.profile.max_battery_mah == 0:
            return False, "Prodotti con batteria non consentiti"
            
        # 5. Controllo Parole Chiave (Materiali, Liquidi, Cosmetici, etc.)
        text_lower = title_or_desc.lower()
        for kw in self.profile.banned_keywords:
            if kw.lower() in text_lower:
                return False, f"Contiene keyword bannata o categoria sensibile: '{kw}'"
                
        return True, ""
        
    def check_margin(self, margin_percent: float) -> bool:
        return margin_percent >= self.profile.min_net_margin_percent

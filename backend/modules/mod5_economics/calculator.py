class FBACalculator:
    # Costanti basate su Amazon Italia
    IVA_PERCENT = 0.22
    AMAZON_REFERRAL_FEE_PERCENT = 0.15  # Costo segnalazione
    PPC_BUDGET_PERCENT = 0.15           # Budget marketing (su fatturato)
    DUTY_TARIC_PERCENT = 0.04           # Dazio stimato
    OCEAN_FREIGHT_ESTIMATE = 1.20       # Nolo marittimo medio per item leggero

    @staticmethod
    def calculate_fba_fee(weight_g: float) -> float:
        """
        Stima tariffa logistica FBA Italia basata sul peso in grammi
        (Semplificata: pacco piccolo vs pacco standard)
        """
        if weight_g <= 300:
            return 4.50
        elif weight_g <= 800:
            return 4.80
        elif weight_g <= 1500:
            return 5.50
        else:
            return 6.50

    @classmethod
    def simulate_margins(cls, buybox_price: float, factory_cost_fob: float, weight_g: float):
        """
        Simula il conto economico del prodotto su Amazon.
        Ritorna un dizionario con tutte le metriche finanziarie.
        """
        # 1. Fatturato Netto
        net_revenue = buybox_price / (1 + cls.IVA_PERCENT)
        
        # 2. Costi Amazon
        referral_fee = net_revenue * cls.AMAZON_REFERRAL_FEE_PERCENT
        fba_fee = cls.calculate_fba_fee(weight_g)
        
        # 3. Costi Prodotto (Landed Cost)
        dazio = factory_cost_fob * cls.DUTY_TARIC_PERCENT
        landed_cost = factory_cost_fob + cls.OCEAN_FREIGHT_ESTIMATE + dazio
        
        # 4. Marketing
        ppc_cost = net_revenue * cls.PPC_BUDGET_PERCENT
        
        # 5. Margine Netto
        net_profit_eur = net_revenue - referral_fee - fba_fee - landed_cost - ppc_cost
        net_margin_percent = (net_profit_eur / net_revenue) * 100 if net_revenue > 0 else 0
        
        return {
            "buybox_price_eur": round(buybox_price, 2),
            "net_revenue_eur": round(net_revenue, 2),
            "referral_fee_eur": round(referral_fee, 2),
            "fba_fee_eur": round(fba_fee, 2),
            "landed_cost_eur": round(landed_cost, 2),
            "ppc_cost_eur": round(ppc_cost, 2),
            "net_profit_eur": round(net_profit_eur, 2),
            "net_margin_percent": round(net_margin_percent, 2)
        }

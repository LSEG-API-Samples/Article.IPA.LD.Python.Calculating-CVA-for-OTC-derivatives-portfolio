from pandas import DataFrame

class SelfEntity:
    def __init__(self, name: str, collateral_currency: str, recovery_instrument: float, 
                 recovery_deal: float, curve_id: str, extended_params=None):
        self.name = name
        self.collateral_currency = collateral_currency
        self.recovery_instrument = recovery_instrument
        self.recovery_deal = recovery_deal
        self.curve_id = curve_id
        self.extended_params = extended_params if extended_params is not None else {}
    
    def to_dict(self):
        return {
            "Name": self.name,
            "CollateralCurrency": self.collateral_currency,
            "RecoveryInstrument": self.recovery_instrument,
            "RecoveryDeal": self.recovery_deal,
            "CurveID": self.curve_id,
            **self.extended_params
        }

class CounterpartyManager:
    def __init__(self):
        self.counterparties = None
    
    def _get_unique_counterparties(self, counterparties):
        unique_counterparties = {}
        for org_id, entries in counterparties.items():
            if org_id:
                unique_counterparties[org_id] = entries[0]
        return unique_counterparties
    
    def get_counterparties(self, counterparties):
        self.counterparties = self._get_unique_counterparties(counterparties)
        return self

    def enhance_counterparty_data(self, reference_entity, enhancement_data):
        enhancement_data = enhancement_data.to_dict()
        if reference_entity not in self.counterparties:
            raise ValueError(f"Counterparty with org_id {reference_entity} does not exist.")
        for key, value in enhancement_data.items():
            self.counterparties[reference_entity][key] = value

    def to_df(self):
        return DataFrame(self.counterparties).T
    
    def to_dict(self):
        return self.counterparties
    
class CounterpartyParams:
    def __init__(self, curve_id, recovery_instrument, recovery_deal, collateral_currency, extended_params=None):
        self.collateral_currency = collateral_currency
        self.curve_id = curve_id
        self.recovery_instrument = recovery_instrument
        self.recovery_deal = recovery_deal
        self.extended_params = extended_params if extended_params is not None else {}

    def to_dict(self):
        return {
            "CurveID": self.curve_id,
            "CollateralCurrency": self.collateral_currency,
            "RecoveryInstrument": self.recovery_instrument,
            "RecoveryDeal": self.recovery_deal,
            **self.extended_params
        }
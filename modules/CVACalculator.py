import warnings
import pandas as pd
from modules.ResponseHandler import EndpointRequest
from datetime import datetime

class CVACalculator:
    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self.universe = None
        self.counterparties = None
        self.entity = None
        self.cva_universe = []
        self.cva_counterparties = {}

    def calculate_cva(self, portfolio,  pricing_parameters, entity):
        try:
            self._reset_state()
            self.entity = entity.to_dict()
            self.universe = portfolio.universe
            self.counterparties = portfolio.counterparties.to_dict()
            request_body = self._prepare_cva_request_body(pricing_parameters)
            cva_endpoint = "data/quantitative-analytics/v1/async-cva"
            cva_response = EndpointRequest.make_request(cva_endpoint, method="POST", body_params=request_body)
            if cva_response.raw.status_code == 202:
                response = EndpointRequest.wait_for_response(cva_response)
                headers_name = [h['name'] for h in response['headers']]
                df = pd.DataFrame(data=response['data'], columns=headers_name)
                return df
            else:
                return cva_response.data.raw
        except Exception as e:
            warnings.warn(f"An error occurred during CVA calculation: {e}")
            return None
        
    def _prepare_cva_request_body(self, pricing_parameters):

        pricing_parameters = pricing_parameters.to_dict()

        self._ensure_valid_universe(pricing_parameters)
        self._filter_counterparties()
        csas = self._generate_csas()
        market_data_assignments = self._generate_market_data_assignments()
        market_data = self._generate_market_data()
        return {
            "outputs": [
                "Headers",
                "Data",
                "MarketData"
            ],
            "fields": [
                "CsaTag",
                "BilateralCvaInReportCcy",
                "BilateralDvaInReportCcy",
                "UnilateralCvaInReportCcy",
                "UnilateralDvaInReportCcy",
                "MarketValueInReportCcyArray",
                "Exposure",
                "PotentialFutureExposure",
                "Allocations",
                "ErrorMessage"
            ],
            "csas": csas,
            "universe": self.cva_universe,
            "pricingParameters": pricing_parameters,
            "marketDataAssignments": market_data_assignments,
            "marketData": market_data
        }


    def _ensure_valid_universe(self, pricing_parameters):
        not_supported_types = {"FxCross", "FxOption", "TermDeposit", "Repo"}
        valuation_date = pricing_parameters["valuationDate"]
        
        for instrument in self.universe:
            if self._is_valid_instrument(instrument, not_supported_types, valuation_date):
                self.cva_universe.append(instrument)
        
        if not self.cva_universe:
            raise ValueError("No valid instruments found for CVA Calculation. Ensure that the instruments have a csaTag assigned and the maturity date is greater than the valuation date.")

    def _is_valid_instrument(self, instrument, not_supported_types, valuation_date):
        instrument_type = instrument['instrumentType']
        if not instrument["csaTag"] and instrument_type not in not_supported_types:
            raise ValueError(f"Instrument {instrument['instrumentDefinition']['instrumentTag']} does not have a csaTag assigned.")
        if instrument_type in not_supported_types:
            warnings.warn(f"Instrument type {instrument_type} is not supported for CVA Calculation. Calculation will be done on supported instruments only.")
            return False
        if "endDate" in instrument["instrumentDefinition"]:
            maturity_date = instrument["instrumentDefinition"]["endDate"]
            if maturity_date < valuation_date:
                warnings.warn(f"Maturity date for instrument with ID {instrument['instrumentDefinition']['instrumentTag']} is earlier than the valuation date of {valuation_date}.")
                return False
        return True
    
    def _filter_counterparties(self):
        existing_counterparties = [instrument["csaTag"] for instrument in self.cva_universe]
        for counterparty, values  in self.counterparties.items():
            counterparty_name = values["name"]
            if counterparty_name in existing_counterparties:
                self.cva_counterparties[counterparty]= values
            else:
                warnings.warn(f"Counterparty with csaTag {counterparty_name} does not exist in the supported universe. CVA calculation will not account for {counterparty_name}.")

    def _generate_csas(self):
        csas = []
        for csaTag, details in self.cva_counterparties.items():
            csas.append(self._create_csa(csaTag, details))
        return csas

    def _create_csa(self, csaTag, details):
        try:
            return {
                "csaTag": details['name'],
                "referenceEntity": csaTag,
                "collateralCcy": details["CollateralCurrency"],
                "counterpartyRecoveryRatePercent": details["RecoveryInstrument"],
                "useCollateral": False
            }
        except KeyError as e:
            raise ValueError(f"Counterparty {details['name']} is missing one or more required parameters: {e}. Use enhance_counterparty_data function to add missing parameters.")

    def _generate_market_data_assignments(self):
        default_probabilities = [{
            "key": {"referenceEntity": self.entity["Name"]},
            "assignmentTag": self.entity["Name"]
        }]
        for csaTag, details in self.cva_counterparties.items():
            default_probabilities.append({
                "key": {"referenceEntity": csaTag},
                "assignmentTag": details["name"]
            })
        return {"credit": {"defaultProbability": default_probabilities}}

    def _generate_market_data(self):
        credit_curves = [self._create_credit_curve(self.entity["Name"], self.entity["CurveID"], self.entity["RecoveryInstrument"])]
        for _, details in self.cva_counterparties.items():
            credit_curves.append(self._create_credit_curve(details["name"], details["CurveID"], details["RecoveryInstrument"]))
        return {"creditCurves": credit_curves}

    def _create_credit_curve(self, assignment_tag, curve_id, recovery_rate):
        return {
            "assignmentTag": assignment_tag,
            "curveDefinition": {
                "referenceEntity": curve_id,
                "referenceEntityType": "ChainRic"
            },
            "curveParameters": {"recoveryRatePercent": recovery_rate}
        }
    
class PricingParameters:
    def __init__(self, valuation_date, simulation_count: int, 
                 self_reference_entity: str, self_recovery_rate_percent: float, 
                 report_ccy: str, numeraire_type = "TerminalZeroCoupon", extended_params=None):
        if isinstance(valuation_date, str):
            self.valuation_date = datetime.fromisoformat(valuation_date)
        elif isinstance(valuation_date, datetime):
            self.valuation_date = valuation_date
        else:
            raise ValueError("valuation_date must be a datetime object or a valid ISO format string")
        
        self.simulation_count = simulation_count
        self.self_reference_entity = self_reference_entity
        self.self_recovery_rate_percent = self_recovery_rate_percent
        self.report_ccy = report_ccy
        self.numeraire_type = numeraire_type
        self.extended_params = extended_params if extended_params is not None else {}

    def to_dict(self):
        return {
            "valuationDate": self.valuation_date.isoformat(),
            "simulationCount": self.simulation_count,
            "selfReferenceEntity": self.self_reference_entity,
            "selfRecoveryRatePercent": self.self_recovery_rate_percent,
            "reportCcy": self.report_ccy,
            "numeraireType": self.numeraire_type,
            **self.extended_params
        }
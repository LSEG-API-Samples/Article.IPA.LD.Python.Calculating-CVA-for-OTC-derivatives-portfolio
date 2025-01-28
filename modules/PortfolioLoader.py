import json
import lseg.data as ld
import pandas as pd
from modules.ResponseHandler import EndpointRequest
from collections import defaultdict
from lseg.data.content import symbol_conversion
from datetime import datetime

class PortfolioLoader:
    def __init__(self):
        self.session = ld.open_session()
        self.scope = self._get_uuid()
        self.portfolio_code = None
        self.transactions = None
        self.universe = None
        self.counterparties = None
    
    def show_portfolios(self):
        portf_endpoint = f"user-data/portfolios/v1/common/{self.scope}"
        portf_response = EndpointRequest.make_request(portf_endpoint).data.raw
        portfolio_data = [{
            'scope': portfolio['id']['scope'],
            'code': portfolio['id']['code'],
            'baseCurrency': portfolio['baseCurrency']
        } for portfolio in portf_response['values']]
        return pd.DataFrame(portfolio_data)
    
    def load_portfolio(self, portfolio_code):
        self.portfolio_code = portfolio_code
        return self

    def load_transactions(self, effective_date = None):
        transactions_endpoint = f"user-data/portfolios/v1/transactionportfolios/{self.scope}/{self.portfolio_code}/transactions"
        if effective_date is not None:
            transactions_endpoint += f"?toTransactionDate={effective_date}"
        transactions_response = EndpointRequest.make_request(transactions_endpoint).data.raw
        self.transactions = {trans['instrumentUid']: trans['counterpartyId'] for trans in transactions_response['values'] if trans['type']=='StockIn'}
        return pd.DataFrame(list(self.transactions.items()), columns=['Instrument ID', 'Counterparty'])

    def load_instruments(self):
        lusid_instruments = self._load_instrument_definitions()
        translated_instruments = self._translate_instruments(lusid_instruments)
        self.counterparties = self._get_counterparty_data(list(self.transactions.values()))
        self.universe = self._build_universe(translated_instruments)
        return self.universe
    
    def set_counterparties(self, counterparties):
        self.counterparties = counterparties

    def _get_uuid(self):
        uuid_endpoint = "user-framework/mobile/user-service/v1/profile/uuid"
        uuid_response = EndpointRequest.make_request(uuid_endpoint).data.raw
        return uuid_response["data"]["uuid"]
    
    def _build_universe(self, translated_instruments):
        for instr_id, instr_def in translated_instruments.items():
            instr_def['instrumentDefinition']['instrumentTag'] = instr_id
            instr_def['csaTag'] = next(
                (item['name'].replace(" ", "")
                for items in self.counterparties.values() 
                for item in items if item['assigned_to'] == instr_id and item['name'] is not None), 
                None
            )
        return list(translated_instruments.values())

    def _load_instrument_definitions(self):
        self._ensure_transactions_loaded()
        instrument_ids = list(self.transactions.keys())
        instruments_endpoint = f"partners/lusid/v1/instruments/$get?identifierType=LusidInstrumentId&scope={self.scope}_{self.portfolio_code}&propertyKeys=Instrument/{self.scope}/AssetType,Instrument/{self.scope}/AssetClass,Instrument/{self.scope}/InstrumentType"
        lusid_instrument_definitions_response = EndpointRequest.make_request(instruments_endpoint, method="POST", body_params=instrument_ids).data.raw
        return {
            lusid_instr_id: lusid_instrument['instrumentDefinition']
            for lusid_instr_id, lusid_instrument in lusid_instrument_definitions_response['values'].items()
        }

    def _ensure_transactions_loaded(self):
        if self.transactions is None:
            self.load_transactions()

    def _translate_instruments(self, instrument_definitions):
        instrument_definitions_translate_endpoint = "partners/lusid/v1/translation/instrumentDefinitions"
        instruments = {
            "instruments": instrument_definitions,
            "dialect": "RefinitivQps"
        }
        instrument_definitions_response = EndpointRequest.make_request(instrument_definitions_translate_endpoint, method="POST", body_params=instruments).data.raw
        return {
            lusid_instrument_id: json.loads(instrument_definition['content'])
            for lusid_instrument_id, instrument_definition in instrument_definitions_response['values'].items()
        }

    def _get_counterparty_data(self, counterparties):
        counterparty_details = symbol_conversion.Definition(
            symbols=list(set(counterparties)),
            from_symbol_type=symbol_conversion.SymbolTypes.OA_PERM_ID,
            to_symbol_types=[
                symbol_conversion.SymbolTypes.RIC,
            ],
        ).get_data().data.raw
        counterparties = defaultdict(list)
        for luid, org_id in self.transactions.items():
            if org_id in counterparty_details['Matches']:
                name = counterparty_details['Matches'][org_id].get('DocumentTitle', '').split(',')[0].replace(" ", "") if counterparty_details['Matches'][org_id].get('DocumentTitle') else org_id
            else:
                name = org_id
            entry = {
                'name': name,
                'assigned_to': luid
            }
            counterparties[org_id].append(entry)
        return counterparties

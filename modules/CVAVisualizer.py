import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

class CVAVisualizer:
    def __init__(self, cva_result):
        self.df = cva_result

    def _prepare_market_value_data(self):
        market_value_data = []
        for idx, market_values in self.df['MarketValueInReportCcyArray'].items():
            for i, value in enumerate(market_values):
                instrument_tag = self.df['Allocations'][idx][i]['instrumentTag']
                market_value_data.append({'CsaTag': self.df['CsaTag'][idx], 'MarketValue': value, 'Instrument': instrument_tag})
        return pd.DataFrame(market_value_data)
    
    def plot_allocations(self, csa_tag = None):
        allocations_df = self.df
        if csa_tag:
            allocations_df = self.df[self.df['CsaTag'] == csa_tag]
        fig = go.Figure(data=[
            go.Bar(name='Bilateral CVA', x=allocations_df['CsaTag'], y=allocations_df['BilateralCvaInReportCcy']),
            go.Bar(name='Bilateral DVA', x=allocations_df['CsaTag'], y=allocations_df['BilateralDvaInReportCcy']),
            go.Bar(name='Unilateral CVA', x=allocations_df['CsaTag'], y=allocations_df['UnilateralCvaInReportCcy']),
            go.Bar(name='Unilateral DVA', x=allocations_df['CsaTag'], y=allocations_df['UnilateralDvaInReportCcy'])
        ])
        fig.update_layout(barmode='group', title='Bilateral and Unilateral CVA and DVA in Report Currency by CSA Tag',
                            xaxis_title='CSA Tag', yaxis_title='Amount in Report Currency')
        fig.show()

    def plot_market_values(self, csa_tag = None):
        market_value_df = self._prepare_market_value_data()
        if csa_tag:
            market_value_df = market_value_df[market_value_df['CsaTag'] == csa_tag]
        fig = px.bar(market_value_df, x='CsaTag', y='MarketValue', color='Instrument',
                     title='Market Value in Report Currency by CSA Tag',
                     labels={'MarketValue': 'Market Value in Report Currency', 'CsaTag': 'CSA Tag'},
                     barmode='group')
        fig.show()

    def plot_potential_future_exposure(self, csa_tag):
        df = pd.DataFrame(self.df[self.df["CsaTag"] == csa_tag]['PotentialFutureExposure'].values[0])
        df['exposureDate'] = pd.to_datetime(df['exposureDate'])
        fig = px.line(df, x='exposureDate', y='expectedBilateralExposure', color='quantilePercent',
                      title=f'Expected Bilateral Exposure Over Time for {csa_tag}',
                      labels={'expectedBilateralExposure': 'Expected Bilateral Exposure', 'exposureDate': 'Exposure Date', 'quantilePercent': 'Quantile Percent'},
                      markers=True)
        fig.show()

    def plot_exposure(self, csa_tag):
        df = pd.DataFrame(self.df[self.df["CsaTag"] == csa_tag]['Exposure'].values[0])
        df['exposureDate'] = pd.to_datetime(df['exposureDate'])
        fig = px.line(df, x='exposureDate', y=['expectedNegativeExposure', 'expectedPositiveExposure'],
                      title=f'Expected Negative and Positive Exposure Over Time for {csa_tag}',
                      labels={'value': 'Exposure', 'exposureDate': 'Exposure Date'},
                      markers=True)
        fig.show()
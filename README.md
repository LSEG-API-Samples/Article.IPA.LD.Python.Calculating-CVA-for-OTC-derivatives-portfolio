## Calculating Credit Valuation Adjustment (CVA) for OTC derivatives portfolio

### Authors: Haykaz Aramyan, Marc Laillat

Credit Valuation Adjustment (CVA) is an important metric in the financial industry, used to account for the counterparty credit risk in derivative transactions. Traditional methods of valuing derivatives often overlook the potential risk of a counterparty defaulting, which can lead to significant financial losses. CVA addresses this gap by adjusting the market value of derivative instruments to reflect the credit risk associated with the counterparties involved.

In recent years, the importance of accurately calculating CVA has grown, driven by regulatory requirements and the need for better risk management practices. Financial institutions are now required to report CVA as part of their risk management and regulatory compliance processes. This requires the development of  models and tools to estimate CVA more accurately.

This article utilizes [async-cva](https://developers.lseg.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/documentation#ipa-financial-contracts-cva-definition) endpoint of LSEG data platform to calculate CVA and leverages a set of custom modules designed to simplify the process. We will detail the PortfolioLoader, CounterpartyManager, CVACalculator, PricingParameters, and CVAVisualizer modules, which together form a system for managing portfolios, counterparty information, and performing CVA calculations. Throughout the article, we will explain these modules in more detail and perform a CVA calculation on a sample portfolio created in MARVAL. MARVAL acts as a trade repository, but you can use your own trade repository and still utilize the async-cva endpoint. As for the CVA calculation methodology, please refer to CVA technical documentation [here](https://developers.lseg.com/content/dam/devportal/cva-technical-documentation.pdf).

It is important to note that the current version of the CVA calculation library supports only Interest Rate Swaps (IRS) and Cross Currency Swaps (CCS).

The full article can be found [here](https://developers.lseg.com/en/article-catalog/article/cva-for-otc-derivatives-portfolio)

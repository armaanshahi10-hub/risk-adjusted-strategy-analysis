# Risk-Adjusted Strategy Analysis

A Python backtesting project that evaluates a rule-based, risk-managed trading strategy against buy-and-hold.

The strategy uses a **core-satellite portfolio structure**:

- **Core (30%)** stays invested at all times  
- **Satellite (70%)** enters and exits based on technical signals  

The objective is to study the trade-off between:

- return  
- drawdown  
- volatility  
- risk-adjusted performance  

---

## Strategy Overview

The satellite portion enters when bullish conditions are confirmed by:

- Supertrend  
- breakout above a recent high  
- volume confirmation  

The satellite exits when conditions weaken through:

- bearish trend change  
- trailing stop logic  
- momentum filter logic  

This creates a portfolio that is always partially invested while actively reducing exposure during weaker market conditions.

---

## Backtest Assumptions

- Initial capital: **$10,000**  
- Execution: **next-day open**  
- Portfolio valuation: **daily close**  
- Core allocation: **30%**  
- Satellite allocation: **70%**  
- Commission: **0.05%**  
- Slippage: **0.05%**  

---

## Project Structure

## Project Structure

```text
risk-adjusted-strategy-analysis/
├── train_test.py
├── multi_asset_test.py
├── requirements.txt
├── README.md
├── src/
│   ├── data.py
│   ├── indicators.py
│   ├── signals.py
│   ├── backtest.py
│   ├── metrics.py
│   └── plots.py
└── outputs/

---

## How to Run

Install dependencies:

bash
pip install -r requirements.txt
python train_test.py
python multi_asset_test.py

---

## Headline Results (SPY)

### Train Period: 2010-01-01 to 2018-12-31

| Metric | Strategy | Buy and Hold |
|---|---:|---:|
| CAGR | 6.45% | 11.32% |
| Sharpe | 0.69 | 0.79 |
| Max Drawdown | -12.37% | -19.35% |

### Test Period: 2019-01-01 to 2024-12-31

| Metric | Strategy | Buy and Hold |
|---|---:|---:|
| CAGR | 12.30% | 17.18% |
| Sharpe | 1.02 | 0.90 |
| Max Drawdown | -14.67% | -33.72% |

---

## Multi-Asset Test

The framework was also tested across:

- SPY  
- QQQ  
- IWM  
- EFA  
- TLT  
- GLD  

This was included to evaluate how the strategy behaves across different asset classes and market environments.

Overall, the strategy generally:

- lowers drawdowns  
- reduces market exposure  
- sometimes improves Sharpe  
- usually trails buy-and-hold in absolute return during strong bull markets  

---

## Key Takeaways

- The strategy is **risk-managed**, not return-maximizing  
- It gives up some upside in strong markets  
- It provides materially better downside control  
- In the SPY test period, it achieved a **higher Sharpe ratio** and **much lower drawdown** than buy-and-hold  

---

## What This Project Demonstrates

- modular Python project structure  
- historical data cleaning and preprocessing  
- technical indicator construction  
- rule-based signal generation  
- portfolio backtesting  
- performance evaluation using CAGR, Sharpe ratio, volatility, and max drawdown  

---

## Notes

This is a research and portfolio project, not a production trading system.

Historical results do not guarantee future performance.





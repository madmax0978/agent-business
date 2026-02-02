# RAG-PEA: Intelligent Portfolio Management System

**Version 1.1.0** - Production-Ready

**AI-Powered Investment Assistant for French PEA (Plan d'Épargne en Actions)**

> Build, manage, and optimize your long-term investment portfolio with multi-agent AI analysis, real-time market data, and automated insights.

---

## Quick Overview

RAG-PEA is a complete financial analysis and portfolio management system that combines:
- **Multi-Agent AI** (CrewAI) for deep market analysis
- **Vector Database** (ChromaDB) for financial document search
- **Real-time Market Data** (Yahoo Finance - Free)
- **Technical Analysis** (RSI, MACD, Bollinger Bands, Support/Resistance)
- **Sentiment Analysis** (Claude AI/GPT-4)
- **Telegram Alerts** for trading opportunities
- **Backtesting Engine** to validate strategies
- **REST API** for easy integration

---

## Key Features

- **Portfolio Builder** - AI constructs optimal PEA portfolios from scratch
- **Smart Document Processing** - Extract key financial data from PDF reports (90%+ compression)
- **Real-time Tracking** - Monitor positions, calculate gains/losses, portfolio health score
- **Technical Signals** - Detect Golden Cross, Death Cross, oversold/overbought zones
- **News Aggregation** - Multi-source news with AI sentiment analysis
- **Automated Alerts** - Telegram notifications for opportunities
- **Backtesting** - Test strategies on historical data before investing
- **Multi-Collection RAG** - Search across dozens of indexed financial reports

---

## Quick Start (5 minutes)

### Prerequisites

- Python 3.9+
- OpenAI API key (for embeddings)
- Optional: Claude API key, NewsAPI key, Telegram bot

### Installation

```bash
# Clone repository
cd RAG-system

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Launch API

```bash
# From project root
python3 api/main.py

# Or with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) - API is ready!

**New in v1.1.0:** Production-ready features with logging, rate limiting, circuit breaker, and more! See [INTEGRATION_TERMINEE.md](INTEGRATION_TERMINEE.md) for details.

### First Steps

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Get market data (no API key needed)
curl http://localhost:8000/market/stock/MC.PA

# 3. Add a position
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 750.00}'

# 4. View portfolio
curl http://localhost:8000/portfolio
```

Done! You now have a working investment tracking system.

---

## Architecture

```
RAG-system/
├── api/
│   ├── main.py                 # FastAPI endpoints (23 routes)
│   ├── rag_manager.py          # ChromaDB + embeddings manager
│   ├── models.py               # Pydantic models
│   ├── agents/                 # CrewAI multi-agent systems
│   │   ├── portfolio_builder_crew.py    # 6 agents for portfolio construction
│   │   ├── financial_crew.py            # 4 agents for analysis
│   │   ├── tools.py                     # RAG, web search tools
│   │   └── advanced_tools.py            # Data collection, optimization
│   ├── services/               # Business logic services
│   │   ├── yahoo_finance_service.py     # Free market data
│   │   ├── technical_analysis.py        # Technical indicators
│   │   ├── sentiment_analyzer.py        # AI sentiment analysis
│   │   ├── news_aggregator.py           # Multi-source news
│   │   ├── portfolio_manager.py         # Portfolio intelligence
│   │   ├── telegram_bot.py              # Telegram notifications
│   │   ├── backtesting_engine.py        # Strategy backtesting
│   │   └── smart_document_processor.py  # AI document extraction
│   └── database/
│       ├── portfolio_db.py              # SQLite manager
│       └── portfolio_manager.py         # Business logic
├── data/
│   ├── vector_db/              # ChromaDB storage
│   ├── documents/              # PDF reports to index
│   └── uploads/                # Uploaded documents
├── docs/
│   └── api-features/           # 20 API endpoint guides
└── scripts/
    └── document_indexer.py     # Batch PDF indexing
```

**See detailed architecture in [ARCHITECTURE.md](ARCHITECTURE.md)**

---

## Use Cases

### 1. Build an Optimal Portfolio

```bash
# AI analyzes market and recommends 10-15 stocks
curl -X POST http://localhost:8000/build-portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 10000,
    "risk_profile": "balanced",
    "sectors": ["technology", "healthcare"],
    "min_companies": 10,
    "max_companies": 15
  }'

# Returns precise allocation and buy orders
```

### 2. Daily Portfolio Monitoring

```python
import requests

# Morning routine
portfolio = requests.get("http://localhost:8000/portfolio").json()
health = requests.get("http://localhost:8000/portfolio/health").json()

print(f"Portfolio value: {portfolio['total_value']}€")
print(f"Health score: {health['health_score']}/100")

if health['health_score'] < 60:
    rebalance = requests.get("http://localhost:8000/portfolio/rebalance").json()
    print(f"Rebalancing needed: {rebalance['recommendations']}")
```

### 3. Analyze a Stock Before Buying

```bash
# Complete analysis: market data + news + sentiment + technical
curl "http://localhost:8000/analysis/complete/AIR.PA?company_name=Airbus"
```

Returns:
- Current price, P/E ratio, dividend yield
- Technical signals (RSI, MACD, support/resistance)
- Recent news sentiment analysis
- Buy/Hold/Sell recommendation with confidence score

### 4. Backtest a Strategy

```python
from api.services.backtesting_engine import BacktestingEngine
from api.services.yahoo_finance_service import YahooFinanceService

# Get historical data
yf = YahooFinanceService()
df = yf.get_historical_data("MC.PA", period="5y")

# Backtest SMA crossover
engine = BacktestingEngine(initial_capital=10000)
results = engine.run_simple_ma_strategy(ticker="MC.PA", historical_data=df)

print(f"Total return: {results['total_return']:.2f}%")
print(f"Sharpe ratio: {results['sharpe_ratio']:.2f}")
print(f"Max drawdown: {results['max_drawdown']:.2f}%")
```

### 5. Search Financial Documents

```bash
# Index a PDF report
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/documents/lvmh_rapport_2024.pdf", "collection_name": "lvmh_2024"}'

# Query the document
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d affaires 2024?",
    "collection_name": "lvmh_2024",
    "n_results": 5,
    "generate_answer": true
  }'
```

---

## API Endpoints

### Portfolio Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/portfolio/add` | Add/update position |
| POST | `/portfolio/sell` | Sell position |
| GET | `/portfolio` | Get complete portfolio |
| GET | `/portfolio/health` | Health score (0-100) |
| GET | `/portfolio/rebalance` | Rebalancing recommendations |
| GET | `/portfolio/position/{ticker}` | Position details |

### Market Data (Free - Yahoo Finance)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/market/stock/{ticker}` | Stock info (price, P/E, dividends) |
| GET | `/market/history/{ticker}` | Historical data |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analysis/technical/{ticker}` | Technical analysis (RSI, MACD, etc.) |
| GET | `/analysis/news/{company}` | Recent news |
| GET | `/analysis/sentiment/{company}` | AI sentiment analysis |
| GET | `/analysis/complete/{ticker}` | All-in-one analysis |

### Documents & RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload and index PDF |
| POST | `/index` | Index existing document |
| POST | `/query` | Query RAG system |
| GET | `/collections` | List all collections |

### AI Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/build-portfolio` | Build optimal portfolio (6 agents) |
| POST | `/analyze/financial-report` | Deep analysis (4 agents) |

**Full API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Configuration

Minimal setup (required):
```bash
# .env
OPENAI_API_KEY=sk-...
```

Full setup (all features):
```bash
# AI Analysis
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# News (100 free requests/day)
NEWSAPI_KEY=your_key

# Telegram Alerts
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=123456789
```

**Full configuration options available in `.env.example`**

---

## Testing

```bash
# Run all tests
pytest

# Test a specific endpoint
curl http://localhost:8000/health
curl http://localhost:8000/market/stock/MC.PA
curl http://localhost:8000/portfolio

# Test portfolio builder (takes 5-10 min)
cd api/agents
python portfolio_builder_crew.py
```

**Full testing guide: [TESTING.md](TESTING.md)**

---

## Documentation

### Essential Documentation

| Document | Description |
|----------|-------------|
| [INTEGRATION_TERMINEE.md](INTEGRATION_TERMINEE.md) | v1.1.0 - Production features & setup |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design (100KB) |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API endpoint reference |
| [TESTING.md](TESTING.md) | Testing guide (40KB) |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute to the project |
| [TELEGRAM_BOT_GUIDE.md](TELEGRAM_BOT_GUIDE.md) | Interactive Telegram bot setup |
| [docs/api-features/](docs/api-features/) | 20 endpoint-specific guides |

### Archived Documentation

Older reports and guides are available in [docs/archives/](docs/archives/)

---

## Key Technologies

- **FastAPI** - Modern Python web framework
- **CrewAI** - Multi-agent orchestration
- **ChromaDB** - Vector database for RAG
- **OpenAI** - Embeddings and analysis
- **Claude AI** - Sentiment analysis
- **yfinance** - Free Yahoo Finance data
- **pandas-ta** - Technical analysis indicators
- **SQLite** - Portfolio storage
- **Telegram Bot** - Push notifications
- **Docling** - Advanced PDF processing

---

## Supported Stocks

25+ French stocks eligible for PEA:

**CAC 40:**
- Luxury: LVMH (MC.PA), Hermès (RMS.PA), Kering (KER.PA)
- Technology: Capgemini (CAP.PA), Dassault Systèmes (DSY.PA)
- Aerospace: Airbus (AIR.PA), Safran (SAF.PA), Thales (HO.PA)
- Industrial: Schneider Electric (SU.PA), Saint-Gobain (SGO.PA)
- Energy: TotalEnergies (TTE.PA), Engie (ENGI.PA)
- Finance: BNP Paribas (BNP.PA), AXA (CS.PA), Société Générale (GLE.PA)
- Healthcare: Sanofi (SAN.PA), EssilorLuxottica (EL.PA)
- Consumer: L'Oréal (OR.PA), Danone (BN.PA), Pernod Ricard (RI.PA)

**Indices:**
- CAC 40: ^FCHI

---

## Limitations

Current limitations:
- Yahoo Finance data: 15-20 min delay
- NewsAPI free tier: 100 requests/day
- Backtesting: Single strategy implemented (SMA crossover)
- Portfolio: Single user (user_id="default_user")
- No broker integration (manual order execution)

Planned improvements:
- WebSocket for real-time data
- More backtesting strategies (RSI, Bollinger, MACD)
- Walk-forward optimization
- Multi-user support
- Broker API integration
- Machine learning predictions

---

## Performance

- API response time: < 100ms (market data)
- RAG search: < 500ms (5 results)
- Portfolio analysis: < 1s
- Technical analysis: < 2s
- CrewAI portfolio builder: 5-10 minutes (comprehensive analysis)
- Document indexing: 5-10 min per 500-page PDF

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Pull request process
- Testing requirements

---

## License

MIT License - Free to use and modify

---

## Support

- **Getting Started:** [Quick Start](#quick-start-5-minutes)
- **Latest Updates:** [INTEGRATION_TERMINEE.md](INTEGRATION_TERMINEE.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Roadmap

**Q1 2026:**
- [ ] Real-time WebSocket data
- [ ] More backtesting strategies
- [ ] Multi-user authentication
- [ ] Web dashboard (React)

**Q2 2026:**
- [ ] Broker integration (Interactive Brokers, Trading212)
- [ ] Machine learning price predictions
- [ ] Mobile app (React Native)
- [ ] PDF report export

---

## Credits

Built with:
- FastAPI by Sebastián Ramírez
- CrewAI by Crew Labs
- ChromaDB by Chroma
- yfinance by Ran Aroussi

---

## Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. Always do your own research and consult a licensed financial advisor before making investment decisions. Past performance does not guarantee future results.

---

**Ready to optimize your investments?** Start with the [Quick Start](#quick-start-5-minutes) above.

**New to v1.1.0?** Check [INTEGRATION_TERMINEE.md](INTEGRATION_TERMINEE.md) for production features.

**Questions?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [API_REFERENCE.md](API_REFERENCE.md).

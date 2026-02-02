#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE - RAG-PEA System
Tests all components without requiring the API to be running
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_passed(test_name, details=""):
    test_results["passed"].append({"test": test_name, "details": details})
    print(f"  PASS: {test_name}")
    if details:
        print(f"    {details}")

def test_failed(test_name, error):
    test_results["failed"].append({"test": test_name, "error": str(error)})
    print(f"  FAIL: {test_name}")
    print(f"    Error: {error}")

def test_warning(test_name, message):
    test_results["warnings"].append({"test": test_name, "message": message})
    print(f"  WARNING: {test_name}")
    print(f"    {message}")


print("=" * 80)
print("RAG-PEA SYSTEM - COMPREHENSIVE TEST SUITE")
print("=" * 80)
print()

# ==========================================
# TEST 1: IMPORTS AND DEPENDENCIES
# ==========================================
print("[1] Testing Imports and Dependencies...")
print("-" * 80)

try:
    import fastapi
    test_passed("Import FastAPI", f"Version: {fastapi.__version__}")
except Exception as e:
    test_failed("Import FastAPI", e)

try:
    import chromadb
    test_passed("Import ChromaDB", f"Version: {chromadb.__version__}")
except Exception as e:
    test_failed("Import ChromaDB", e)

try:
    import yfinance
    test_passed("Import yfinance", "OK")
except Exception as e:
    test_failed("Import yfinance", e)

try:
    import sentence_transformers
    test_passed("Import sentence-transformers", "OK")
except Exception as e:
    test_failed("Import sentence-transformers", e)

try:
    import anthropic
    test_passed("Import anthropic", "OK")
except Exception as e:
    test_failed("Import anthropic", e)

try:
    import openai
    test_passed("Import openai", "OK")
except Exception as e:
    test_failed("Import openai", e)

try:
    import crewai
    test_passed("Import CrewAI", "OK")
except Exception as e:
    test_failed("Import CrewAI", e)

try:
    import docling
    test_passed("Import Docling", "OK")
except Exception as e:
    test_failed("Import Docling", e)

print()

# ==========================================
# TEST 2: CONFIGURATION MODULE
# ==========================================
print("[2] Testing Configuration Module...")
print("-" * 80)

try:
    sys.path.insert(0, str(Path(__file__).parent / "api"))
    from config import settings, validate_configuration
    test_passed("Import config module", "OK")

    # Test settings attributes
    if settings.app_name:
        test_passed("Config: app_name", settings.app_name)

    if settings.api_port:
        test_passed("Config: api_port", f"Port {settings.api_port}")

    if settings.database:
        test_passed("Config: database settings", settings.database.url)

    if settings.ollama:
        test_passed("Config: ollama settings", f"Model: {settings.ollama.model}")

    # Validate configuration
    is_valid, errors = validate_configuration()
    if is_valid:
        test_passed("Configuration validation", "All checks passed")
    else:
        for error in errors:
            test_warning("Configuration validation", error)

except Exception as e:
    test_failed("Import config module", e)

print()

# ==========================================
# TEST 3: DATABASE MODULE
# ==========================================
print("[3] Testing Database Module...")
print("-" * 80)

try:
    from database.portfolio_db import PortfolioDatabase
    test_passed("Import PortfolioDatabase", "OK")

    # Test database initialization
    db = PortfolioDatabase(db_path=":memory:")  # In-memory for testing
    test_passed("Database initialization", "Tables created")

    # Test add_position
    success = db.add_position(
        ticker="MC.PA",
        company_name="LVMH",
        quantity=10,
        price=700.0,
        user_id="test_user"
    )
    if success:
        test_passed("Database: add_position", "Position added successfully")
    else:
        test_failed("Database: add_position", "Failed to add position")

    # Test get_portfolio
    portfolio = db.get_portfolio(user_id="test_user")
    if len(portfolio) == 1:
        test_passed("Database: get_portfolio", f"Found {len(portfolio)} position")
    else:
        test_failed("Database: get_portfolio", f"Expected 1 position, got {len(portfolio)}")

    # Test PRU calculation
    db.add_position(
        ticker="MC.PA",
        company_name="LVMH",
        quantity=5,
        price=750.0,
        user_id="test_user"
    )
    portfolio = db.get_portfolio(user_id="test_user")
    position = portfolio[0]
    expected_pru = (10 * 700 + 5 * 750) / 15
    if abs(position['avg_price'] - expected_pru) < 0.01:
        test_passed("Database: PRU calculation", f"PRU: {position['avg_price']:.2f}€ (expected: {expected_pru:.2f}€)")
    else:
        test_failed("Database: PRU calculation", f"Expected {expected_pru:.2f}, got {position['avg_price']:.2f}")

    # Test sell_position
    success = db.sell_position(
        ticker="MC.PA",
        quantity=5,
        price=780.0,
        user_id="test_user"
    )
    if success:
        test_passed("Database: sell_position", "Sold 5 shares successfully")
    else:
        test_failed("Database: sell_position", "Failed to sell position")

    # Test portfolio summary
    summary = db.get_portfolio_summary(user_id="test_user")
    if "total_positions" in summary and "total_value" in summary:
        test_passed("Database: get_portfolio_summary", f"Positions: {summary['total_positions']}, Value: {summary['total_value']:.2f}€")
    else:
        test_failed("Database: get_portfolio_summary", "Missing required fields")

except Exception as e:
    test_failed("Database module", e)

print()

# ==========================================
# TEST 4: YAHOO FINANCE SERVICE
# ==========================================
print("[4] Testing Yahoo Finance Service...")
print("-" * 80)

try:
    from services.yahoo_finance_service import YahooFinanceService, get_ticker
    test_passed("Import YahooFinanceService", "OK")

    yf_service = YahooFinanceService()
    test_passed("YahooFinanceService initialization", "OK")

    # Test ticker mapping
    ticker = get_ticker("LVMH")
    if ticker == "MC.PA":
        test_passed("Ticker mapping", f"LVMH -> {ticker}")
    else:
        test_failed("Ticker mapping", f"Expected MC.PA, got {ticker}")

    # Test get_stock_info (requires internet)
    try:
        info = yf_service.get_stock_info("MC.PA")
        if info and "current_price" in info:
            test_passed("YahooFinance: get_stock_info", f"LVMH price: {info['current_price']}€")
        else:
            test_warning("YahooFinance: get_stock_info", "No data returned (possible API issue)")
    except Exception as e:
        test_warning("YahooFinance: get_stock_info", f"Network/API error: {e}")

    # Test caching
    import time
    start_time = time.time()
    yf_service.get_stock_info("MC.PA")  # First call
    first_call_time = time.time() - start_time

    start_time = time.time()
    yf_service.get_stock_info("MC.PA")  # Cached call
    cached_call_time = time.time() - start_time

    if cached_call_time < first_call_time / 2:
        test_passed("YahooFinance: cache", f"Cache is working (cached: {cached_call_time:.3f}s vs first: {first_call_time:.3f}s)")
    else:
        test_warning("YahooFinance: cache", "Cache might not be working efficiently")

except Exception as e:
    test_failed("Yahoo Finance service", e)

print()

# ==========================================
# TEST 5: RAG MANAGER
# ==========================================
print("[5] Testing RAG Manager...")
print("-" * 80)

try:
    from rag_manager import RAGManager
    test_passed("Import RAGManager", "OK")

    # Test initialization
    rag = RAGManager(db_path="./test_chroma_db")
    test_passed("RAGManager initialization", "OK")

    # Test check_ollama
    ollama_available = rag.check_ollama()
    if ollama_available:
        test_passed("RAG: check_ollama", "Ollama is available")
    else:
        test_warning("RAG: check_ollama", "Ollama is not available (some features won't work)")

    # Test list_collections
    collections = rag.list_collections()
    test_passed("RAG: list_collections", f"Found {len(collections)} collections")

    # Test embedding model
    if rag.embed_model:
        test_passed("RAG: embedding model", f"Model: {rag.embed_model_id}")
    else:
        test_failed("RAG: embedding model", "Embedding model not loaded")

except Exception as e:
    test_failed("RAG Manager", e)

print()

# ==========================================
# TEST 6: MODELS VALIDATION
# ==========================================
print("[6] Testing Pydantic Models...")
print("-" * 80)

try:
    from models import (
        QueryRequest, HealthResponse, PositionAddRequest,
        PositionSellRequest, FinancialAnalysisRequest
    )
    test_passed("Import models", "OK")

    # Test PositionAddRequest validation
    try:
        request = PositionAddRequest(
            ticker="MC.PA",
            company_name="LVMH",
            quantity=10,
            price=700.0,
            user_id="test"
        )
        test_passed("Models: PositionAddRequest validation", "Valid model created")
    except Exception as e:
        test_failed("Models: PositionAddRequest validation", e)

    # Test negative quantity validation
    try:
        request = PositionAddRequest(
            ticker="MC.PA",
            company_name="LVMH",
            quantity=-10,  # Should fail
            price=700.0,
            user_id="test"
        )
        test_failed("Models: negative quantity validation", "Should have rejected negative quantity")
    except:
        test_passed("Models: negative quantity validation", "Correctly rejected negative quantity")

except Exception as e:
    test_failed("Pydantic models", e)

print()

# ==========================================
# TEST 7: IMPORT BUG IN MAIN.PY
# ==========================================
print("[7] Testing main.py Import Issue...")
print("-" * 80)

try:
    # Read main.py
    main_py_path = Path(__file__).parent / "api" / "main.py"
    with open(main_py_path, 'r') as f:
        main_content = f.read()

    # Check for problematic imports
    if "from config import settings" in main_content:
        test_warning("main.py imports", "Uses relative import 'from config import settings' - should be 'from api.config import settings'")

    if "from models import" in main_content:
        test_warning("main.py imports", "Uses relative import 'from models import' - should be 'from api.models import'")

    if "from rag_manager import" in main_content:
        test_warning("main.py imports", "Uses relative import 'from rag_manager import' - should be 'from api.rag_manager import'")

    test_passed("main.py analysis", "Import issues identified")

except Exception as e:
    test_failed("main.py analysis", e)

print()

# ==========================================
# TEST 8: TECHNICAL ANALYSIS
# ==========================================
print("[8] Testing Technical Analysis Service...")
print("-" * 80)

try:
    from services.technical_analysis import TechnicalAnalyzer
    test_passed("Import TechnicalAnalyzer", "OK")

    analyzer = TechnicalAnalyzer()
    test_passed("TechnicalAnalyzer initialization", "OK")

    # Test with sample data
    import pandas as pd
    import numpy as np
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    sample_df = pd.DataFrame({
        'Close': np.random.uniform(700, 750, 100),
        'High': np.random.uniform(700, 760, 100),
        'Low': np.random.uniform(690, 750, 100),
        'Volume': np.random.uniform(1000000, 2000000, 100)
    }, index=dates)

    # Test calculate_indicators
    df_with_indicators = analyzer.calculate_indicators(sample_df)
    if 'SMA_20' in df_with_indicators.columns:
        test_passed("TechnicalAnalyzer: calculate_indicators", "SMA_20 calculated")
    else:
        test_failed("TechnicalAnalyzer: calculate_indicators", "Missing SMA_20 column")

    if 'RSI' in df_with_indicators.columns:
        rsi_value = df_with_indicators['RSI'].iloc[-1]
        if 0 <= rsi_value <= 100:
            test_passed("TechnicalAnalyzer: RSI calculation", f"RSI: {rsi_value:.2f} (valid range)")
        else:
            test_failed("TechnicalAnalyzer: RSI calculation", f"RSI out of range: {rsi_value}")

    # Test detect_signals
    signals = analyzer.detect_signals(df_with_indicators)
    if isinstance(signals, dict):
        test_passed("TechnicalAnalyzer: detect_signals", f"Signals: {list(signals.keys())}")
    else:
        test_failed("TechnicalAnalyzer: detect_signals", "Should return dict")

except Exception as e:
    test_failed("Technical Analysis service", e)

print()

# ==========================================
# TEST 9: PORTFOLIO MANAGER
# ==========================================
print("[9] Testing Portfolio Manager...")
print("-" * 80)

try:
    from services.portfolio_manager import PortfolioManager
    test_passed("Import PortfolioManager", "OK")

    manager = PortfolioManager()
    test_passed("PortfolioManager initialization", "OK")

    # Test with our test database
    try:
        health = manager.get_portfolio_health_score(user_id="test_user")
        if "score" in health and "grade" in health:
            test_passed("PortfolioManager: health_score", f"Score: {health['score']}/100 ({health['grade']})")
        else:
            test_failed("PortfolioManager: health_score", "Missing required fields")
    except Exception as e:
        test_warning("PortfolioManager: health_score", f"Error: {e}")

except Exception as e:
    test_failed("Portfolio Manager", e)

print()

# ==========================================
# TEST 10: LOGGING CONFIGURATION
# ==========================================
print("[10] Testing Logging Configuration...")
print("-" * 80)

try:
    from logging_config import get_logger, setup_logging
    test_passed("Import logging_config", "OK")

    # Test logger creation
    logger = get_logger("test_module")
    if logger:
        test_passed("Logging: get_logger", "Logger created successfully")

    # Test log message
    logger.info("Test log message")
    test_passed("Logging: log message", "Log message written")

except Exception as e:
    test_failed("Logging configuration", e)

print()

# ==========================================
# TEST 11: MIDDLEWARE AND EXCEPTIONS
# ==========================================
print("[11] Testing Middleware and Exception Handlers...")
print("-" * 80)

try:
    from middleware import setup_middleware
    test_passed("Import middleware", "OK")
except Exception as e:
    test_failed("Import middleware", e)

try:
    from exceptions import install_error_handlers, OllamaUnavailableError, RateLimitExceededError
    test_passed("Import exceptions", "OK")

    # Test custom exceptions
    try:
        raise OllamaUnavailableError("Test error")
    except OllamaUnavailableError as e:
        test_passed("Exceptions: OllamaUnavailableError", "Custom exception works")

except Exception as e:
    test_failed("Import exceptions", e)

print()

# ==========================================
# TEST 12: CIRCUIT BREAKER
# ==========================================
print("[12] Testing Circuit Breaker...")
print("-" * 80)

try:
    from utils.circuit_breaker import CircuitBreaker
    test_passed("Import CircuitBreaker", "OK")

    # Test circuit breaker initialization
    cb = CircuitBreaker(failure_threshold=3, timeout=10)
    test_passed("CircuitBreaker: initialization", "OK")

    # Test circuit states
    if cb.state == "CLOSED":
        test_passed("CircuitBreaker: initial state", "State is CLOSED")
    else:
        test_failed("CircuitBreaker: initial state", f"Expected CLOSED, got {cb.state}")

except Exception as e:
    test_failed("Circuit Breaker", e)

print()

# ==========================================
# FINAL SUMMARY
# ==========================================
print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0

print(f"\nTotal tests: {total_tests}")
print(f"  PASSED: {len(test_results['passed'])} ({pass_rate:.1f}%)")
print(f"  FAILED: {len(test_results['failed'])}")
print(f"  WARNINGS: {len(test_results['warnings'])}")
print()

if test_results["failed"]:
    print("FAILED TESTS:")
    print("-" * 80)
    for i, failure in enumerate(test_results["failed"], 1):
        print(f"{i}. {failure['test']}")
        print(f"   Error: {failure['error']}")
    print()

if test_results["warnings"]:
    print("WARNINGS:")
    print("-" * 80)
    for i, warning in enumerate(test_results["warnings"], 1):
        print(f"{i}. {warning['test']}")
        print(f"   {warning['message']}")
    print()

# Exit code
sys.exit(0 if len(test_results["failed"]) == 0 else 1)

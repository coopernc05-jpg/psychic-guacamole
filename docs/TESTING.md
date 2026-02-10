# Testing Guide

Comprehensive guide for testing the Polymarket Arbitrage Bot.

## Table of Contents

1. [Test Setup](#test-setup)
2. [Running Tests](#running-tests)
3. [Test Structure](#test-structure)
4. [Writing Tests](#writing-tests)
5. [Coverage Reports](#coverage-reports)
6. [Integration Testing](#integration-testing)
7. [Mock Data](#mock-data)

## Test Setup

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Test Environment

Create a `.env.test` file for test-specific configuration:

```bash
# Test environment variables
POLYMARKET_API_KEY=test_key
PRIVATE_KEY=test_private_key
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with detailed output on failures
pytest tests/ -v --tb=long
```

### Specific Test Files

```bash
# Run specific test file
pytest tests/test_strategies.py

# Run specific test class
pytest tests/test_strategies.py::TestCrossMarketArbitrage

# Run specific test function
pytest tests/test_strategies.py::TestCrossMarketArbitrage::test_detect_arbitrage
```

### Coverage

```bash
# Run with coverage
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Continuous Testing

```bash
# Watch for changes and re-run tests
pytest-watch tests/
```

## Test Structure

```
tests/
├── __init__.py
├── test_strategies.py        # Arbitrage strategy tests
├── test_detector.py           # Opportunity detection tests
├── test_position_sizing.py    # Position sizing tests
├── test_polymarket_api.py     # API client tests
├── test_performance.py        # Performance tracking tests
├── test_dashboard.py          # Dashboard tests
└── integration/
    ├── __init__.py
    └── test_end_to_end.py     # End-to-end integration tests
```

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows

## Writing Tests

### Basic Test Template

```python
import pytest
from src.arbitrage.strategies.cross_market import CrossMarketArbitrage

class TestCrossMarketArbitrage:
    """Tests for cross-market arbitrage strategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance for testing."""
        return CrossMarketArbitrage()
    
    def test_initialization(self, strategy):
        """Test strategy initializes correctly."""
        assert strategy is not None
        assert strategy.min_profit_margin > 0
    
    def test_detect_arbitrage(self, strategy):
        """Test arbitrage detection."""
        # Arrange
        markets = create_test_markets()
        
        # Act
        opportunities = strategy.detect(markets)
        
        # Assert
        assert len(opportunities) > 0
        assert opportunities[0].expected_profit > 0
```

### Async Tests

```python
import pytest
from src.market.polymarket_api import PolymarketAPIClient

class TestPolymarketAPI:
    """Tests for Polymarket API client."""
    
    @pytest.mark.asyncio
    async def test_get_markets(self):
        """Test fetching markets."""
        client = PolymarketAPIClient()
        markets = await client.get_markets(limit=10)
        
        assert len(markets) <= 10
        assert all(m.market_id for m in markets)
```

### Mocking

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.execution.executor import TradeExecutor

class TestTradeExecutor:
    """Tests for trade executor."""
    
    @pytest.mark.asyncio
    @patch('src.execution.executor.PolymarketAPIClient')
    async def test_execute_trade(self, mock_api):
        """Test trade execution with mocked API."""
        # Setup mock
        mock_api.return_value.place_order = AsyncMock(return_value={
            'order_id': '123',
            'status': 'filled'
        })
        
        # Execute
        executor = TradeExecutor(api_client=mock_api())
        result = await executor.execute_trade(...)
        
        # Assert
        assert result['order_id'] == '123'
        mock_api.return_value.place_order.assert_called_once()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("win_prob,expected_return,expected_fraction", [
    (0.6, 1.5, 0.2),  # Positive edge
    (0.5, 1.0, 0.0),  # Break-even
    (0.4, 1.5, 0.0),  # Negative edge
])
def test_kelly_criterion(win_prob, expected_return, expected_fraction):
    """Test Kelly Criterion with various inputs."""
    from src.execution.position_sizing import CapitalAllocator
    
    allocator = CapitalAllocator(initial_capital=1000)
    fraction = allocator._calculate_kelly_fraction(win_prob, expected_return)
    
    assert abs(fraction - expected_fraction) < 0.01
```

### Fixtures

```python
import pytest
from src.market.market_data import Market, Token, OrderBook

@pytest.fixture
def sample_market():
    """Create a sample market for testing."""
    return Market(
        market_id="test_market",
        question="Will it rain tomorrow?",
        tokens=[
            Token(token_id="yes", outcome="YES", price=0.55),
            Token(token_id="no", outcome="NO", price=0.45)
        ]
    )

@pytest.fixture
def sample_orderbook():
    """Create a sample orderbook."""
    return OrderBook(
        token_id="yes",
        bids=[(0.54, 100), (0.53, 200)],
        asks=[(0.56, 150), (0.57, 250)]
    )

def test_market_validation(sample_market):
    """Test using fixtures."""
    assert sample_market.market_id == "test_market"
    assert len(sample_market.tokens) == 2
```

## Coverage Reports

### Generate Coverage

```bash
# Terminal report
pytest --cov=src tests/

# HTML report (recommended)
pytest --cov=src --cov-report=html tests/

# XML report (for CI)
pytest --cov=src --cov-report=xml tests/

# JSON report
pytest --cov=src --cov-report=json tests/
```

### Coverage Goals

- **Overall:** >80% code coverage
- **Critical paths:** 100% coverage
  - Arbitrage strategies
  - Risk management
  - Position sizing
  - Trade execution

### Viewing Coverage

```bash
# View HTML report
open htmlcov/index.html

# View in terminal with missing lines
pytest --cov=src --cov-report=term-missing tests/
```

## Integration Testing

### End-to-End Test Example

```python
# tests/integration/test_end_to_end.py
import pytest
from src.main import Bot
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_workflow():
    """Test complete bot workflow: detect → execute → track."""
    
    # Mock API to return test data
    with patch('src.market.polymarket_api.PolymarketAPIClient') as mock_api:
        # Setup mock responses
        mock_api.return_value.get_markets = AsyncMock(return_value=[
            create_test_market(market_id="1"),
            create_test_market(market_id="2")
        ])
        
        # Create bot
        bot = Bot(mode="alert")
        
        # Run detection cycle
        await bot.detect_opportunities()
        
        # Verify opportunities were detected
        assert len(bot.opportunities) > 0
        
        # Verify logging
        assert bot.opportunity_logger.opportunities[-1] is not None
```

### Running Integration Tests

```bash
# Run only integration tests
pytest tests/integration/ -v

# Run with marker
pytest -m integration tests/
```

## Mock Data

### Creating Mock Markets

```python
from src.market.market_data import Market, Token

def create_test_market(
    market_id="test_1",
    yes_price=0.55,
    no_price=0.45
):
    """Create a test market with specified prices."""
    return Market(
        market_id=market_id,
        question="Test question?",
        tokens=[
            Token(token_id=f"{market_id}_yes", outcome="YES", price=yes_price),
            Token(token_id=f"{market_id}_no", outcome="NO", price=no_price)
        ],
        volume=10000,
        liquidity=5000
    )

def create_arbitrage_opportunity():
    """Create markets with arbitrage opportunity."""
    return [
        create_test_market(market_id="1", yes_price=0.48, no_price=0.50),  # Sum < 1
        create_test_market(market_id="2", yes_price=0.52, no_price=0.50)   # Can arbitrage
    ]
```

### Using Mock Data in Tests

```python
def test_yes_no_imbalance_detection():
    """Test YES/NO imbalance detection."""
    from src.arbitrage.strategies.yes_no_imbalance import YesNoImbalanceArbitrage
    
    strategy = YesNoImbalanceArbitrage()
    markets = [create_test_market(yes_price=0.45, no_price=0.50)]  # Sum = 0.95
    
    opportunities = strategy.detect(markets)
    
    assert len(opportunities) > 0
    assert opportunities[0].expected_profit > 0
```

## Best Practices

### 1. Test Isolation

- Each test should be independent
- Use fixtures for common setup
- Clean up after tests

### 2. Descriptive Names

```python
# Good
def test_kelly_criterion_returns_zero_for_negative_edge():
    pass

# Bad
def test_kelly():
    pass
```

### 3. AAA Pattern

```python
def test_something():
    # Arrange - Set up test data
    market = create_test_market()
    strategy = CrossMarketArbitrage()
    
    # Act - Execute the code being tested
    result = strategy.detect([market])
    
    # Assert - Verify the results
    assert len(result) > 0
```

### 4. Edge Cases

Test boundary conditions:
- Empty inputs
- Zero values
- Very large values
- Invalid data
- Network failures

### 5. Async Testing

```python
@pytest.mark.asyncio
async def test_async_function():
    """Always mark async tests with @pytest.mark.asyncio."""
    result = await some_async_function()
    assert result is not None
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop
- Pull requests
- Before deployment

See `.github/workflows/test.yml` for CI configuration.

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/psychic-guacamole
pytest tests/
```

**Async test failures:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Coverage not working:**
```bash
# Install pytest-cov
pip install pytest-cov
```

## Adding New Tests

When adding new features:

1. Write tests first (TDD)
2. Run tests to see them fail
3. Implement feature
4. Run tests to see them pass
5. Check coverage
6. Commit tests with feature

## Test Checklist

Before committing:

- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Coverage >80% for new code
- [ ] No skipped tests without reason
- [ ] Integration tests pass
- [ ] Documentation updated

---

**Remember:** Good tests are as important as good code. They ensure reliability and make refactoring safer.

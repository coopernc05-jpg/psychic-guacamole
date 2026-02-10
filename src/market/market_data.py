"""Market data models and structures."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class MarketStatus(Enum):
    """Market status enumeration."""

    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    SUSPENDED = "suspended"


class OrderSide(Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class Market:
    """Represents a Polymarket market."""

    market_id: str
    question: str
    description: str
    category: str
    end_date: datetime
    status: MarketStatus
    yes_price: float
    no_price: float
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float
    volume_24h: float
    liquidity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def spread(self) -> float:
        """Calculate the bid-ask spread."""
        return (self.yes_ask - self.yes_bid) + (self.no_ask - self.no_bid)

    @property
    def price_sum(self) -> float:
        """Sum of YES and NO prices (should be ~1.0)."""
        return self.yes_price + self.no_price

    def to_dict(self) -> Dict[str, Any]:
        """Convert market to dictionary."""
        return {
            "market_id": self.market_id,
            "question": self.question,
            "description": self.description,
            "category": self.category,
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "yes_bid": self.yes_bid,
            "yes_ask": self.yes_ask,
            "no_bid": self.no_bid,
            "no_ask": self.no_ask,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "metadata": self.metadata,
        }


@dataclass
class OrderBook:
    """Order book for a market outcome."""

    market_id: str
    outcome: str  # "YES" or "NO"
    bids: list[tuple[float, float]]  # [(price, size), ...]
    asks: list[tuple[float, float]]  # [(price, size), ...]
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def best_bid(self) -> Optional[tuple[float, float]]:
        """Get best bid (highest price)."""
        return max(self.bids, key=lambda x: x[0]) if self.bids else None

    @property
    def best_ask(self) -> Optional[tuple[float, float]]:
        """Get best ask (lowest price)."""
        return min(self.asks, key=lambda x: x[0]) if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        """Calculate mid price."""
        best_bid = self.best_bid
        best_ask = self.best_ask
        if best_bid and best_ask:
            return (best_bid[0] + best_ask[0]) / 2
        return None


@dataclass
class Trade:
    """Represents a trade execution."""

    trade_id: str
    market_id: str
    outcome: str
    side: OrderSide
    price: float
    size: float
    timestamp: datetime
    gas_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        """Total cost including gas."""
        return (self.price * self.size) + self.gas_cost

    @property
    def net_amount(self) -> float:
        """Net amount (positive for buys, negative for sells)."""
        if self.side == OrderSide.BUY:
            return -self.total_cost
        else:
            return self.price * self.size


@dataclass
class Position:
    """Represents a trading position."""

    position_id: str
    market_id: str
    outcome: str
    size: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pnl: Optional[float] = None
    gas_costs: float = 0.0

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.exit_price is not None:
            return 0.0  # Position is closed
        return (self.current_price - self.entry_price) * self.size - self.gas_costs

    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.exit_price is None

    @property
    def return_pct(self) -> float:
        """Calculate return percentage."""
        if self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return ((self.current_price - self.entry_price) / self.entry_price) * 100

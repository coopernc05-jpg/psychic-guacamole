#!/usr/bin/env python3
"""Quick test script to verify Polymarket API integration."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.market.polymarket_api import PolymarketAPIClient


async def test_api():
    """Test the Polymarket API client."""
    print("Loading configuration...")
    config = load_config()
    
    print(f"Gamma API URL: https://gamma-api.polymarket.com")
    print(f"CLOB API URL: {config.polymarket_api_url}")
    print(f"API Key: {'Set' if config.polymarket_api_key else 'Not set'}")
    print()
    
    print("Initializing API client...")
    client = PolymarketAPIClient(config)
    
    try:
        await client.connect()
        print("✓ Connected to API\n")
        
        print("Fetching markets (limit=10)...")
        markets = await client.get_markets(limit=10)
        
        print(f"\n{'='*80}")
        print(f"RESULTS: Fetched {len(markets)} markets")
        print(f"{'='*80}\n")
        
        if markets:
            print("Sample markets:")
            for i, market in enumerate(markets[:5], 1):
                print(f"\n{i}. {market.question[:70]}...")
                print(f"   Market ID: {market.market_id}")
                print(f"   Category: {market.category}")
                print(f"   Status: {market.status.value}")
                print(f"   YES Price: ${market.yes_price:.3f} (Bid: ${market.yes_bid:.3f}, Ask: ${market.yes_ask:.3f})")
                print(f"   NO Price:  ${market.no_price:.3f} (Bid: ${market.no_bid:.3f}, Ask: ${market.no_ask:.3f})")
                print(f"   Volume 24h: ${market.volume_24h:,.2f}")
                print(f"   Liquidity: ${market.liquidity:,.2f}")
                print(f"   Price Sum: {market.price_sum:.3f} (should be ~1.0)")
        else:
            print("❌ No markets fetched! Check API configuration and logs.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()
        print("\n✓ Closed API connection")


if __name__ == "__main__":
    asyncio.run(test_api())

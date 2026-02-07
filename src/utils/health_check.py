"""Health check system for bot monitoring."""

from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from loguru import logger


class HealthChecker:
    """System health monitoring."""
    
    def __init__(self):
        """Initialize health checker."""
        self.start_time = datetime.now()
        self.last_api_check: Optional[datetime] = None
        self.api_healthy = False
    
    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()
    
    async def check_api_connectivity(self, api_url: str = "https://gamma-api.polymarket.com/ping") -> bool:
        """Check Polymarket API connectivity.
        
        Args:
            api_url: API endpoint to check
            
        Returns:
            True if API is reachable
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.api_healthy = response.status == 200
                    self.last_api_check = datetime.now()
                    return self.api_healthy
        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            self.api_healthy = False
            self.last_api_check = datetime.now()
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status.
        
        Returns:
            Dictionary with health status information
        """
        uptime = self.get_uptime_seconds()
        
        return {
            "status": "healthy" if self.api_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "api_status": {
                "healthy": self.api_healthy,
                "last_check": self.last_api_check.isoformat() if self.last_api_check else None
            }
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format.
        
        Args:
            seconds: Uptime in seconds
            
        Returns:
            Formatted uptime string
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)


# Global health checker instance
health_checker = HealthChecker()

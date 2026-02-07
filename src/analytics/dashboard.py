"""Flask-based web dashboard for real-time monitoring and control."""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from threading import Thread

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging

from .performance import PerformanceTracker
from .logger import OpportunityLogger, ExecutionLogger


class Dashboard:
    """Web dashboard for bot monitoring and control."""

    def __init__(
        self,
        performance_tracker: PerformanceTracker,
        opportunity_logger: OpportunityLogger,
        execution_logger: ExecutionLogger,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False,
    ):
        """Initialize dashboard.

        Args:
            performance_tracker: Performance tracking instance
            opportunity_logger: Opportunity logging instance
            execution_logger: Execution logging instance
            host: Host to bind to
            port: Port to bind to
            debug: Debug mode flag
        """
        self.performance_tracker = performance_tracker
        self.opportunity_logger = opportunity_logger
        self.execution_logger = execution_logger
        self.host = host
        self.port = port
        self.debug = debug

        # Create Flask app
        self.app = Flask(
            __name__, template_folder=str(Path(__file__).parent / "templates")
        )
        self.app.config["SECRET_KEY"] = "polymarket-arbitrage-bot-secret"

        # Disable Flask's default logger in production
        if not debug:
            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)

        # Enable CORS
        CORS(self.app)

        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Recent activities cache
        self.recent_opportunities: List[Dict[str, Any]] = []
        self.recent_trades: List[Dict[str, Any]] = []

        # Setup routes
        self._setup_routes()
        self._setup_socketio_handlers()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def index():
            """Serve main dashboard page."""
            return render_template("dashboard.html")

        @self.app.route("/api/metrics")
        def get_metrics():
            """Get current performance metrics."""
            metrics = self.performance_tracker.calculate_metrics()
            market_stats = self.performance_tracker.get_market_statistics()

            return jsonify(
                {
                    "metrics": metrics.to_dict(),
                    "market_stats": market_stats,
                    "capital": {
                        "initial": self.performance_tracker.initial_capital,
                        "current": self.performance_tracker.current_capital,
                    },
                }
            )

        @self.app.route("/api/opportunities")
        def get_opportunities():
            """Get recent opportunities."""
            stats = self.opportunity_logger.get_statistics()
            return jsonify(
                {
                    "statistics": stats,
                    "recent": self.recent_opportunities[-50:],  # Last 50
                }
            )

        @self.app.route("/api/trades")
        def get_trades():
            """Get recent trades."""
            stats = self.execution_logger.get_trade_statistics()
            position_stats = self.execution_logger.get_position_statistics()

            return jsonify(
                {
                    "trade_statistics": stats,
                    "position_statistics": position_stats,
                    "recent_trades": self.recent_trades[-50:],  # Last 50
                }
            )

        @self.app.route("/api/equity-curve")
        def get_equity_curve():
            """Get equity curve data for chart."""
            curve_data = [
                {"timestamp": dt.isoformat(), "value": value}
                for dt, value in self.performance_tracker.equity_curve
            ]
            return jsonify(curve_data)

        @self.app.route("/api/logs")
        def get_logs():
            """Get recent log entries."""
            # Read recent log files
            log_dir = Path("data/opportunities")
            logs = []

            if log_dir.exists():
                log_files = sorted(log_dir.glob("*.jsonl"), reverse=True)[
                    :3
                ]  # Last 3 days
                for log_file in log_files:
                    with open(log_file, "r") as f:
                        for line in f:
                            try:
                                logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass

            return jsonify(logs[-100:])  # Last 100 entries

        @self.app.route("/api/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": (
                        datetime.now() - self.performance_tracker.equity_curve[0][0]
                    ).total_seconds(),
                }
            )

        @self.app.route("/api/config", methods=["GET", "POST"])
        def config():
            """Get or update configuration."""
            if request.method == "POST":
                # Note: This is a placeholder. Real implementation would update config
                return jsonify(
                    {
                        "status": "success",
                        "message": "Configuration update not implemented",
                    }
                )
            else:
                # Return current config (placeholder)
                return jsonify(
                    {"mode": "alert", "strategies_enabled": ["all"], "min_profit": 5.0}
                )

    def _setup_socketio_handlers(self):
        """Setup SocketIO event handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            emit("connection_response", {"data": "Connected to dashboard"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            pass

        @self.socketio.on("request_update")
        def handle_update_request():
            """Handle real-time data update request."""
            self.broadcast_update()

    def broadcast_update(self):
        """Broadcast real-time update to all connected clients."""
        metrics = self.performance_tracker.calculate_metrics()
        self.socketio.emit("metrics_update", metrics.to_dict())

    def log_opportunity(self, opportunity_data: Dict[str, Any]):
        """Log new opportunity and broadcast to dashboard.

        Args:
            opportunity_data: Opportunity data dictionary
        """
        self.recent_opportunities.append(opportunity_data)
        self.socketio.emit("new_opportunity", opportunity_data)

    def log_trade(self, trade_data: Dict[str, Any]):
        """Log new trade and broadcast to dashboard.

        Args:
            trade_data: Trade data dictionary
        """
        self.recent_trades.append(trade_data)
        self.socketio.emit("new_trade", trade_data)
        self.broadcast_update()  # Update metrics after trade

    def run(self):
        """Run the dashboard server."""
        print(f"🚀 Dashboard starting at http://{self.host}:{self.port}")
        print(f"📊 Open your browser to view real-time metrics")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=self.debug)

    def run_in_thread(self):
        """Run dashboard in a separate thread (non-blocking)."""
        thread = Thread(target=self.run, daemon=True)
        thread.start()
        return thread


def create_dashboard(
    performance_tracker: PerformanceTracker,
    opportunity_logger: OpportunityLogger,
    execution_logger: ExecutionLogger,
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = False,
) -> Dashboard:
    """Factory function to create dashboard instance.

    Args:
        performance_tracker: Performance tracking instance
        opportunity_logger: Opportunity logging instance
        execution_logger: Execution logging instance
        host: Host to bind to
        port: Port to bind to
        debug: Debug mode flag

    Returns:
        Dashboard instance
    """
    return Dashboard(
        performance_tracker=performance_tracker,
        opportunity_logger=opportunity_logger,
        execution_logger=execution_logger,
        host=host,
        port=port,
        debug=debug,
    )

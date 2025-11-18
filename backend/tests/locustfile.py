"""
Load testing script using locust
"""
from locust import HttpUser, task, between
import random


class TradingBotUser(HttpUser):
    """Simulated user for load testing"""

    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Called when a user starts"""
        # Register and login
        username = f"user_{random.randint(1000, 9999)}"
        user_data = {
            "email": f"{username}@test.com",
            "username": username,
            "password": "testpass123",
        }

        # Register
        self.client.post("/api/v1/auth/register", json=user_data)

        # Login
        login_data = {"username": username, "password": "testpass123"}
        response = self.client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def headers(self):
        """Get auth headers"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def list_bots(self):
        """List all bots"""
        self.client.get("/api/v1/bots/", headers=self.headers())

    @task(2)
    def list_strategies(self):
        """List all strategies"""
        self.client.get("/api/v1/strategies/", headers=self.headers())

    @task(1)
    def create_bot(self):
        """Create a new bot"""
        bot_data = {
            "name": f"Load Test Bot {random.randint(1, 1000)}",
            "exchange": "binance",
            "trading_pair": random.choice(["BTC/USDT", "ETH/USDT", "BNB/USDT"]),
            "initial_capital": random.randint(1000, 10000),
            "max_position_size": 10.0,
            "stop_loss_percentage": 5.0,
            "take_profit_percentage": 10.0,
        }
        response = self.client.post("/api/v1/bots/", json=bot_data, headers=self.headers())

        if response.status_code == 201:
            bot_id = response.json()["id"]
            # Get bot details
            self.client.get(f"/api/v1/bots/{bot_id}", headers=self.headers())

    @task(1)
    def get_market_data(self):
        """Get market ticker"""
        symbol = random.choice(["BTC/USDT", "ETH/USDT", "BNB/USDT"])
        self.client.get(f"/api/v1/market/ticker/binance/{symbol}")

    @task(4)
    def health_check(self):
        """Check health endpoint"""
        self.client.get("/health")


class AdminUser(HttpUser):
    """Simulated admin user"""

    wait_time = between(2, 5)
    token = None

    def on_start(self):
        """Login as admin"""
        login_data = {"username": "admin", "password": "admin123"}
        response = self.client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task
    def monitor_system(self):
        """Monitor system health"""
        self.client.get("/api/v1/health/detailed", headers=self.headers())

    @task
    def view_all_bots(self):
        """View all bots in system"""
        self.client.get("/api/v1/bots/", headers=self.headers())

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_bot(client: AsyncClient, test_user):
    """Test creating a trading bot."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    bot_data = {
        "name": "Test Bot",
        "description": "Test bot description",
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "initial_capital": 10000,
        "max_position_size": 10.0,
        "stop_loss_percentage": 5.0,
        "take_profit_percentage": 10.0,
    }

    response = await client.post("/api/v1/bots/", json=bot_data, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == bot_data["name"]
    assert data["exchange"] == bot_data["exchange"]
    assert data["status"] == "stopped"


@pytest.mark.asyncio
async def test_list_bots(client: AsyncClient, test_user):
    """Test listing user's bots."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create a bot first
    bot_data = {
        "name": "Test Bot",
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "initial_capital": 10000,
    }
    await client.post("/api/v1/bots/", json=bot_data, headers=headers)

    # List bots
    response = await client.get("/api/v1/bots/", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_bot(client: AsyncClient, test_user):
    """Test getting a specific bot."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create a bot
    bot_data = {
        "name": "Test Bot",
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "initial_capital": 10000,
    }
    create_response = await client.post("/api/v1/bots/", json=bot_data, headers=headers)
    bot_id = create_response.json()["id"]

    # Get the bot
    response = await client.get(f"/api/v1/bots/{bot_id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == bot_id
    assert data["name"] == bot_data["name"]


@pytest.mark.asyncio
async def test_delete_bot(client: AsyncClient, test_user):
    """Test deleting a bot."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create a bot
    bot_data = {
        "name": "Test Bot",
        "exchange": "binance",
        "trading_pair": "BTC/USDT",
        "initial_capital": 10000,
    }
    create_response = await client.post("/api/v1/bots/", json=bot_data, headers=headers)
    bot_id = create_response.json()["id"]

    # Delete the bot
    response = await client.delete(f"/api/v1/bots/{bot_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(f"/api/v1/bots/{bot_id}", headers=headers)
    assert response.status_code == 404

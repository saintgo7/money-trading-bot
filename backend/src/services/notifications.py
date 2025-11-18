from typing import Dict, List, Optional
from enum import Enum
from loguru import logger
from datetime import datetime


class NotificationType(str, Enum):
    TRADE_EXECUTED = "trade_executed"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_REACHED = "take_profit_reached"
    DAILY_REPORT = "daily_report"
    ERROR = "error"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    SLACK = "slack"


class NotificationService:
    """Service for sending notifications to users"""

    def __init__(self):
        self.channels: Dict[NotificationChannel, bool] = {
            NotificationChannel.EMAIL: True,
            NotificationChannel.WEBHOOK: False,
            NotificationChannel.TELEGRAM: False,
            NotificationChannel.SLACK: False,
        }

    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ):
        """
        Send notification to user

        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data
            channels: Channels to send to (default: all enabled)
        """
        if channels is None:
            channels = [ch for ch, enabled in self.channels.items() if enabled]

        logger.info(
            f"Sending {notification_type} notification to user {user_id}: {title}"
        )

        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email(user_id, title, message, data)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook(user_id, notification_type, title, message, data)
                elif channel == NotificationChannel.TELEGRAM:
                    await self._send_telegram(user_id, title, message, data)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack(user_id, title, message, data)
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {e}")

    async def _send_email(
        self, user_id: int, title: str, message: str, data: Optional[Dict]
    ):
        """Send email notification"""
        # TODO: Implement email sending with SMTP or SendGrid
        logger.debug(f"Would send email to user {user_id}: {title}")

    async def _send_webhook(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict],
    ):
        """Send webhook notification"""
        # TODO: Implement webhook POST request
        logger.debug(f"Would send webhook to user {user_id}: {title}")

    async def _send_telegram(
        self, user_id: int, title: str, message: str, data: Optional[Dict]
    ):
        """Send Telegram notification"""
        # TODO: Implement Telegram bot message
        logger.debug(f"Would send Telegram message to user {user_id}: {title}")

    async def _send_slack(
        self, user_id: int, title: str, message: str, data: Optional[Dict]
    ):
        """Send Slack notification"""
        # TODO: Implement Slack webhook
        logger.debug(f"Would send Slack message to user {user_id}: {title}")

    async def notify_trade_executed(
        self, user_id: int, bot_name: str, symbol: str, side: str, quantity: float, price: float
    ):
        """Notify when a trade is executed"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TRADE_EXECUTED,
            title=f"Trade Executed: {bot_name}",
            message=f"{side.upper()} {quantity} {symbol} at ${price}",
            data={
                "bot_name": bot_name,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
            },
        )

    async def notify_bot_started(self, user_id: int, bot_name: str):
        """Notify when a bot is started"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.BOT_STARTED,
            title=f"Bot Started: {bot_name}",
            message=f"Your trading bot '{bot_name}' has been started successfully.",
            data={"bot_name": bot_name},
        )

    async def notify_bot_stopped(self, user_id: int, bot_name: str, reason: str = "Manual"):
        """Notify when a bot is stopped"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.BOT_STOPPED,
            title=f"Bot Stopped: {bot_name}",
            message=f"Your trading bot '{bot_name}' has been stopped. Reason: {reason}",
            data={"bot_name": bot_name, "reason": reason},
        )

    async def notify_stop_loss_triggered(
        self, user_id: int, bot_name: str, symbol: str, loss: float
    ):
        """Notify when stop loss is triggered"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.STOP_LOSS_TRIGGERED,
            title=f"Stop Loss Triggered: {bot_name}",
            message=f"Stop loss triggered for {symbol}. Loss: ${loss:.2f}",
            data={"bot_name": bot_name, "symbol": symbol, "loss": loss},
        )

    async def notify_take_profit_reached(
        self, user_id: int, bot_name: str, symbol: str, profit: float
    ):
        """Notify when take profit is reached"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TAKE_PROFIT_REACHED,
            title=f"Take Profit Reached: {bot_name}",
            message=f"Take profit reached for {symbol}. Profit: ${profit:.2f}",
            data={"bot_name": bot_name, "symbol": symbol, "profit": profit},
        )

    async def notify_daily_report(
        self,
        user_id: int,
        total_pnl: float,
        trades_today: int,
        win_rate: float,
        active_bots: int,
    ):
        """Send daily performance report"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.DAILY_REPORT,
            title="Daily Trading Report",
            message=f"Today's P&L: ${total_pnl:.2f} | Trades: {trades_today} | Win Rate: {win_rate:.1f}% | Active Bots: {active_bots}",
            data={
                "total_pnl": total_pnl,
                "trades_today": trades_today,
                "win_rate": win_rate,
                "active_bots": active_bots,
            },
        )

    async def notify_error(self, user_id: int, bot_name: str, error_message: str):
        """Notify when an error occurs"""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ERROR,
            title=f"Error in {bot_name}",
            message=f"An error occurred: {error_message}",
            data={"bot_name": bot_name, "error": error_message},
        )


# Global notification service instance
notification_service = NotificationService()

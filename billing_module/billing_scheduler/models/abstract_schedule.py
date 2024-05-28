from abc import ABC, abstractmethod


class AbstractSchedule(ABC):
    """Service for handling scheduled tasks."""

    @abstractmethod
    async def send_notification_no_auto_pay_job(self) -> None:
        """
        Send notifications to users without auto-pay enabled.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def send_notification_no_active_card(self) -> None:
        """
        Send notifications to users without an active card.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def send_notification_tomorrow_auto_pay(self) -> None:
        """
        Send notifications to users with auto-pay scheduled for tomorrow.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def check_transaction_status(self) -> None:
        """
        Check the status of transactions.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def send_notification_to_user(self, user_id: str, pattern_id: str) -> None:
        """
        Send a notification to a specific user.

        Args:
            user_id (str): The user ID.
            pattern_id (str): The pattern ID for the notification.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def check_payment_status(self, transaction_id: str) -> None:
        """
        Check the payment status for a specific transaction.

        Args:
            transaction_id (str): The transaction ID.

        Returns:
            None
        """
        pass

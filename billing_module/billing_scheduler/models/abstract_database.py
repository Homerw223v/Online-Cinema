from abc import ABC, abstractmethod
from uuid import UUID


class AbstractDatabase(ABC):
    """
    Service for interacting with the database and retrieving payment-related information.
    """

    @abstractmethod
    async def get_users_with_no_auto_pay(self) -> list[UUID]:
        """
        Retrieve users who do not have auto-pay enabled
        and have subscriptions expiring in 2-3 days.

        Returns:
            list[UUID]: List results containing users UUID without auto-pay.
        """
        pass

    @abstractmethod
    async def get_users_with_no_active_card(self) -> list[UUID]:
        """
        Retrieve users with auto-pay enabled whose subscriptions expire in 2-3 days
        but have no active payment method.

        Returns:
            list[UUID]: List result containing users UUID with no active card.
        """
        pass

    @abstractmethod
    async def get_users_with_tomorrow_payment_auto_pay(self) -> list[UUID]:
        """
        Retrieve users with auto-pay enabled
        whose subscriptions expire in 1-2 days.

        Returns:
            list[UUID]: List result containing users UUID with auto-pay scheduled for tomorrow.
        """
        pass

    @abstractmethod
    async def get_transactions_with_waiting_payment_status(self) -> list[UUID]:
        """
        Retrieve transactions with waiting payment status
        and select the latest one for each transaction ID.

        Returns:
            list[UUID]: The result containing transactions UUID with pending status.
        """
        pass

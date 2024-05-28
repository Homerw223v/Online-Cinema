from db.postgres import async_session
from services.repositories import TransactionsService, UserSubscriptionService, UserPaymentMethodService
from services.payment import PaymentService, RefundService


async def get_payment_service():
    async with async_session() as session:
        yield PaymentService(TransactionsService(session))


async def get_refund_service():
    async with async_session() as session:
        yield RefundService(TransactionsService(session))


async def get_user_subscriptions_service():
    async with async_session() as session:
        yield UserSubscriptionService(session)


async def get_user_payment_methods_service():
    async with async_session() as session:
        yield UserPaymentMethodService(session)

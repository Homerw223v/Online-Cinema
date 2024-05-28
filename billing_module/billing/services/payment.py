from uuid import UUID
from services.repositories import TransactionsService
from db.models import Transaction, TransactionState
from yookassa import Payment, Refund
from yookassa import Configuration
from core.config import settings
from schemas import RetrievePaymentDTO, PaymentProviderStateDTO, UserPaymentMethodDTO
from utils import PaymentState

Configuration.account_id = settings.yookassa.account_id
Configuration.secret_key = settings.yookassa.secret_key


class BasePaymentService:
    def __init__(self, service_db: TransactionsService):
        self.service_db = service_db

    async def get_transaction(self, transaction_id: UUID):
        return await self.service_db.get_by_id(transaction_id)


class PaymentService(BasePaymentService):

    async def start(self, entity):
        model = await self.service_db.create(entity)
        await self.service_db.change_state(model, TransactionState.TRANSACTION_START.name)
        return model

    async def create(self, model: Transaction):
        payment_params = {
            "amount": {"value": model.tariff.price, "currency": "RUB"},
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": f"{settings.yookassa.redirect_url}?transaction_id={model.id}",
            },
            "description": f"Оплата {model.tariff.name}",
        }
        user_payment_method = await self.service_db.get_user_payment_method(model.user_id)
        if user_payment_method:
            payment_params["payment_method_id"] = str(user_payment_method.payment_id)
        else:
            payment_params["user_payment_method"] = {"type": "bank_card"}
        payment = Payment.create(payment_params, model.id)

        # get confirmation url
        confirmation_url = None if user_payment_method else payment.confirmation.confirmation_url
        await self.service_db.set_payment_id(model, payment.id)
        await self.service_db.change_state(model, TransactionState.PAYMENT_WAIT.name)
        return RetrievePaymentDTO(
            id=model.id,
            user_id=model.user_id,
            tariff_id=model.tariff_id,
            confirmation_url=confirmation_url,
        )

    async def save_payment_method(self, method: UserPaymentMethodDTO):
        await self.service_db.save_user_payment_method(method)

    async def check_state(self, transaction_id: UUID): # noqa!
        model = await self.get_transaction(transaction_id)
        payment = Payment.find_one(str(model.payment_id))
        actual_state = await self.service_db.actual_state(transaction_id)
        if actual_state == TransactionState.PAYMENT_WAIT:
            if payment.status == PaymentState.SUCCEEDED.value:
                if payment.payment_method.saved and payment.payment_method.type == "bank_card":
                    user_payment = UserPaymentMethodDTO(
                        user_id=model.user_id,
                        payment_id=payment.payment_method.id,
                        type=payment.payment_method.type,
                        title=payment.payment_method.title,
                    )
                    await self.save_payment_method(user_payment)
                await self.service_db.change_state(model, TransactionState.PAYMENT_SUCCESS.name, commit=False)
                await self.service_db.activate_subscription(model)

            elif payment.status == PaymentState.CANCELED.value:
                if hasattr(payment.payment_method, "id"): # noqa!
                    await self.service_db.deactivate_user_payment_method(payment.payment_method.id)
                await self.service_db.change_state(model, TransactionState.PAYMENT_CANCELED.name)
                await self.service_db.change_state(model, TransactionState.TRANSACTION_COMPLETE.name)
        return PaymentProviderStateDTO(id=payment.id, state=payment.status)


class RefundService(BasePaymentService):
    async def start(self, entity):
        model = await self.get_transaction(entity.transaction_id)
        await self.service_db.change_state(model, TransactionState.TRANSACTION_START.name)
        return model

    async def create(self, model: Transaction):
        refund = Refund.create(
            {"amount": {"value": model.tariff.price, "currency": "RUB"}, "payment_id": model.payment_id},
        )
        payment = Payment.find_one(str(model.payment_id))
        if payment.status == PaymentState.SUCCEEDED.value:
            await self.service_db.change_state(model, TransactionState.REFUND_SUCCESS.name, commit=False)
            await self.service_db.decrease_subscription(model)

        elif payment.status == PaymentState.CANCELED.value:
            await self.service_db.change_state(model, TransactionState.PAYMENT_CANCELED.name)
            await self.service_db.change_state(model, TransactionState.TRANSACTION_COMPLETE.name)
        return PaymentProviderStateDTO(id=refund.id, state=refund.status)

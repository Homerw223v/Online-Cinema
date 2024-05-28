from db.models import (
    History,
    Subscription,
    UserPaymentMethod,
    Tariff,
    Transaction,
    UserSubscription,
    UserFreezeSubscription,
)
from sqladmin import ModelView


class MixinExcludeClass:
    form_excluded_columns = ["created_at"]
    column_default_sort = ("created_at", True)
    page_size = 25
    page_size_options = [25, 50, 100, 200]


class SubscribersAdmin(MixinExcludeClass, ModelView, model=Subscription):
    column_list = [
        Subscription.name,
        Subscription.tariffs,
    ]
    column_sortable_list = [
        Subscription.name,
    ]
    column_labels = {
        Subscription.name: "Name",
        Subscription.tariffs: "Tariffs",
    }


class TariffsAdmin(MixinExcludeClass, ModelView, model=Tariff):
    column_list = [
        Tariff.name,
        Tariff.subscription,
        Tariff.duration,
        Tariff.duration_unit,
        Tariff.price,
        Tariff.repeat,
    ]
    column_labels = {
        Tariff.name: "Name",
        Tariff.subscription: "Subscription",
        Tariff.duration: "Duration",
        Tariff.duration_unit: "Duration unit",
        Tariff.price: "Price",
        Tariff.repeat: "Repeat",
    }


class TransactionsAdmin(MixinExcludeClass, ModelView, model=Transaction):
    column_list = [
        Transaction.user_id,
        Transaction.payment_id,
        Transaction.tariff,
        Transaction.id,
    ]
    column_labels = {
        Transaction.user_id: "User Id",
        Transaction.payment_id: "Payment Id",
        Transaction.tariff: "Tariff name",
        Transaction.id: "Transaction id",
    }


class UserSubscriptionAdmin(MixinExcludeClass, ModelView, model=UserSubscription):
    column_list = [
        UserSubscription.subscription,
        UserSubscription.user_id,
        UserSubscription.expired,
    ]
    column_labels = {
        UserSubscription.subscription: "Subscription",
        UserSubscription.user_id: "User Id",
        UserSubscription.expired: "Expire on",
    }


class UserFreezeSubscriptionAdmin(MixinExcludeClass, ModelView, model=UserFreezeSubscription):
    column_list = [
        UserFreezeSubscription.subscription,
        UserFreezeSubscription.user_id,
        UserFreezeSubscription.freeze_days,
    ]
    column_labels = {
        UserFreezeSubscription.subscription: "Subscription",
        UserFreezeSubscription.user_id: "User Id",
        UserFreezeSubscription.freeze_days: "Freeze days",
    }


class HistoryAdmin(MixinExcludeClass, ModelView, model=History):
    name = "History"
    name_plural = "Histories"
    column_sortable_list = ["created_at"]
    column_list = [
        "created_at",
        "state",
        "transaction.user_id",
        "transaction.tariff",
        "transaction_id",
    ]
    column_labels = {
        "transaction.user_id": "User id",
        "transaction.tariff": "Tariff name",
        "state": "State",
        "created_at": "Created at",
        "transaction_id": "Transaction id",
    }


class UserCardAdmin(MixinExcludeClass, ModelView, model=UserPaymentMethod):
    column_list = [UserPaymentMethod.user_id, UserPaymentMethod.title, UserPaymentMethod.type, UserPaymentMethod.active]
    column_sortable_list = [UserPaymentMethod.created_at]
    column_labels = {
        UserPaymentMethod.user_id: "User id",
        UserPaymentMethod.title: "Title",
        UserPaymentMethod.type: "Payment type",
        UserPaymentMethod.active: "Active",
    }

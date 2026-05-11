import enum

class TransactionType(str, enum.Enum):
    monetary = "monetary"
    service = "service"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    awaiting_confirmation = "awaiting_confirmation"
    settled = "settled"
    rejected = "rejected"
    auto_settled = "auto_settled"
    cancelled = "cancelled"
    disputed = "disputed"
"""Validated financial contracts. Projections cannot mutate this ledger state."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

MAX_MONEY = 100_000_000_000
BUSINESS_TZ = timezone(timedelta(hours=5, minutes=30), "Asia/Kolkata")
Amount = Annotated[int, Field(strict=True, gt=0, le=MAX_MONEY)]
Nonnegative = Annotated[int, Field(strict=True, ge=0, le=MAX_MONEY)]
Identifier = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]


def money(value: str) -> int:
    try:
        amount = Decimal(value)
        if not amount.is_finite() or amount < 0 or amount * 100 > MAX_MONEY:
            raise ValueError("Invalid monetary amount")
        return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary amount") from exc


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True,
                              json_schema_serialization_defaults_required=True)


class Terms(Contract):
    allow_partial: bool = True
    minimum_partial_paise: Amount = 3000000
    partial_days: int = Field(default=3, ge=1, le=30)
    allow_deferral: bool = True
    defer_days: int = Field(default=3, ge=1, le=30)
    late_penalty_paise: Nonnegative = 200000


class Obligation(Contract):
    id: Identifier
    label: str = Field(min_length=1, max_length=100)
    amount_paise: Amount
    paid_paise: Nonnegative = 0
    due_date: date
    mandatory: bool = True
    terms: Terms | None = None

    @model_validator(mode="after")
    def consistent(self) -> "Obligation":
        if self.paid_paise > self.amount_paise:
            raise ValueError("Amount cannot be below paid amount")
        return self

    @property
    def outstanding_paise(self) -> int:
        return self.amount_paise - self.paid_paise


class Receivable(Contract):
    id: Identifier
    label: str = Field(min_length=1, max_length=100)
    amount_paise: Amount
    received_paise: Nonnegative = 0
    created_date: date
    expected_date: date
    status: Literal["expected", "confirmed", "settled"] = "expected"
    historical_late_rate: float = Field(default=0.35, ge=0, le=1, allow_inf_nan=False)
    historical_delay_days: float = Field(default=2, ge=0, le=60, allow_inf_nan=False)

    @model_validator(mode="after")
    def consistent(self) -> "Receivable":
        if self.expected_date < self.created_date or self.received_paise > self.amount_paise:
            raise ValueError("Invalid receivable dates or settlement")
        if (self.status == "settled") != (self.received_paise == self.amount_paise):
            raise ValueError("Settled status must match received amount")
        return self


class Proposal(Contract):
    id: Identifier
    obligation_id: Identifier
    amount_paise: Amount


class State(Contract):
    business_id: str = "demo"
    business_name: str = "Morrow Studio"
    currency: Literal["INR"] = "INR"
    timezone: str = "Asia/Kolkata"
    base_date: date = date(2026, 10, 17)
    cash_paise: Nonnegative = 10000000
    reserve_paise: Nonnegative = 1000000
    generation: int = 1
    version: int = 0
    obligations: dict[str, Obligation] = Field(default_factory=dict)
    receivables: dict[str, Receivable] = Field(default_factory=dict)
    proposals: dict[str, Proposal] = Field(default_factory=dict)


def baseline(generation: int = 1) -> State:
    return State(generation=generation, obligations={
        "supplier": Obligation(id="supplier", label="Evergreen Supplies", amount_paise=6000000,
                               due_date=date(2026, 10, 17), mandatory=False, terms=Terms()),
        "operations": Obligation(id="operations", label="Payroll & operating costs", amount_paise=5000000,
                                 due_date=date(2026, 10, 18)),
    }, receivables={
        "customer": Receivable(id="customer", label="Northstar Retail · INV-1042", amount_paise=4000000,
                               created_date=date(2026, 10, 3), expected_date=date(2026, 10, 18)),
    }, proposals={"proposal": Proposal(id="proposal", obligation_id="supplier", amount_paise=6000000)})


class EventBase(Contract):
    event_id: Identifier
    business_id: Identifier
    timestamp: datetime
    currency: Literal["INR"] = "INR"

    @field_validator("timestamp")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone required")
        return value.astimezone(timezone.utc)


class PaymentProposed(EventBase):
    type: Literal["PAYMENT_PROPOSED"]
    proposal: Proposal


class PaymentConfirmed(EventBase):
    type: Literal["PAYMENT_CONFIRMED"]
    obligation_id: Identifier
    amount_paise: Amount


class ExpenseRecorded(EventBase):
    type: Literal["EXPENSE_RECORDED"]
    obligation: Obligation


class ReceivableCreated(EventBase):
    type: Literal["RECEIVABLE_CREATED"]
    receivable: Receivable


class ReceivableDelayed(EventBase):
    type: Literal["RECEIVABLE_DELAYED"]
    receivable_id: Identifier
    expected_date: date


class ReceivableReceived(EventBase):
    type: Literal["RECEIVABLE_RECEIVED"]
    receivable_id: Identifier
    amount_paise: Amount


class ObligationUpdated(EventBase):
    type: Literal["OBLIGATION_UPDATED"]
    obligation_id: Identifier
    amount_paise: Amount | None = None
    due_date: date | None = None
    terms: Terms | None = None

    @model_validator(mode="after")
    def nonempty(self) -> "ObligationUpdated":
        if all(value is None for value in (self.amount_paise, self.due_date, self.terms)):
            raise ValueError("At least one update is required")
        return self


Event = Annotated[PaymentProposed | PaymentConfirmed | ExpenseRecorded | ReceivableCreated |
                  ReceivableDelayed | ReceivableReceived | ObligationUpdated, Field(discriminator="type")]
EventAdapter: TypeAdapter[Event] = TypeAdapter(Event)


def apply_event(state: State, event: Event) -> State:
    """Pure reducer. Event-ID idempotency belongs to the transactional event store."""
    if event.business_id != state.business_id:
        raise ValueError("Wrong business")
    origin = datetime.combine(state.base_date, datetime.min.time(), tzinfo=BUSINESS_TZ).astimezone(timezone.utc)
    if event.timestamp < origin:
        raise ValueError("Event predates baseline")
    if event.timestamp > datetime.now(timezone.utc):
        raise ValueError("Future events cannot settle the current ledger")
    result = state.model_copy(deep=True)
    if isinstance(event, PaymentProposed):
        obligation = result.obligations.get(event.proposal.obligation_id)
        if obligation is None:
            raise ValueError("Unknown obligation")
        if event.proposal.amount_paise > obligation.outstanding_paise:
            raise ValueError("Proposal exceeds outstanding obligation")
        result.proposals[event.proposal.id] = event.proposal.model_copy(deep=True)
    elif isinstance(event, PaymentConfirmed):
        obligation = result.obligations.get(event.obligation_id)
        if obligation is None:
            raise ValueError("Unknown obligation")
        if event.amount_paise > obligation.outstanding_paise:
            raise ValueError("Payment exceeds outstanding obligation")
        if event.amount_paise > result.cash_paise:
            raise ValueError("Insufficient settled cash")
        result.cash_paise -= event.amount_paise
        obligation.paid_paise += event.amount_paise
        for identifier, proposal in list(result.proposals.items()):
            if proposal.obligation_id == obligation.id:
                if not obligation.outstanding_paise:
                    del result.proposals[identifier]
                else:
                    proposal.amount_paise = min(proposal.amount_paise, obligation.outstanding_paise)
    elif isinstance(event, ExpenseRecorded):
        if event.obligation.id in result.obligations or event.obligation.paid_paise:
            raise ValueError("Duplicate obligation or pre-settled expense")
        result.obligations[event.obligation.id] = event.obligation.model_copy(deep=True)
    elif isinstance(event, ReceivableCreated):
        if event.receivable.created_date > event.timestamp.astimezone(BUSINESS_TZ).date():
            raise ValueError("Invoice creation date is after its recorded event")
        if event.receivable.id in result.receivables or event.receivable.received_paise:
            raise ValueError("Duplicate receivable or pre-settled invoice")
        result.receivables[event.receivable.id] = event.receivable.model_copy(deep=True)
    elif isinstance(event, (ReceivableReceived, ReceivableDelayed)):
        receivable = result.receivables.get(event.receivable_id)
        if receivable is None:
            raise ValueError("Unknown receivable")
        if receivable.created_date > event.timestamp.astimezone(BUSINESS_TZ).date():
            raise ValueError("Event predates invoice creation")
        if receivable.status == "settled":
            raise ValueError("Receivable already settled")
        values = receivable.model_dump()
        if isinstance(event, ReceivableReceived):
            received = receivable.received_paise + event.amount_paise
            if received > receivable.amount_paise:
                raise ValueError("Receipt exceeds outstanding receivable")
            values.update(received_paise=received,
                          status="settled" if received == receivable.amount_paise else receivable.status)
            result.cash_paise += event.amount_paise
        else:
            if event.expected_date <= receivable.expected_date:
                raise ValueError("Delay must move expected date later")
            values.update(expected_date=event.expected_date)
        result.receivables[event.receivable_id] = Receivable.model_validate(values)
    elif isinstance(event, ObligationUpdated):
        obligation = result.obligations.get(event.obligation_id)
        if obligation is None:
            raise ValueError("Unknown obligation")
        values = obligation.model_dump()
        values.update(event.model_dump(exclude_none=True, include={"amount_paise", "due_date", "terms"}))
        result.obligations[event.obligation_id] = Obligation.model_validate(values)
    result.version += 1
    return result


def replay(state: State, events: list[Event]) -> State:
    seen: dict[str, str] = {}
    result = state.model_copy(deep=True)
    for item in sorted(events, key=lambda event: event.timestamp):
        payload = item.model_dump_json()
        if item.event_id in seen:
            if seen[item.event_id] != payload:
                raise ValueError("Event identity conflict")
            continue
        seen[item.event_id] = payload
        result = apply_event(result, item)
    return result

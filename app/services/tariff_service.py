import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.tariff_repo import TariffRepository
from app.utils.exceptions import BadRequestException


def month_end_date(billing_month: str) -> date:
    """'YYYY-MM' -> last calendar day of that month (used to resolve which
    tariff row is 'effective' for a billing period)."""
    year, month = (int(part) for part in billing_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def calculate_slab_charge(
    db: Session, connection_type: str, units_consumed: Decimal, billing_month: str
) -> tuple[Decimal, Decimal]:
    """
    Applies slab-based pricing: total units are split across contiguous
    slabs (e.g. 0-100 @ rate1, 100-200 @ rate2, 200-500 @ rate3, 500+ @ rate4)
    and each portion is billed at its own rate. Returns (energy_charge, fixed_charge).
    Slab boundaries are treated as contiguous (a slab's `maximum_units` equals
    the next slab's `minimum_units`); the fixed_charge applied is that of the
    highest slab actually reached.
    """
    repo = TariffRepository(db)
    as_of = month_end_date(billing_month)
    slabs = repo.get_slabs(connection_type, as_of)

    if not slabs:
        raise BadRequestException(
            f"No active tariff found for connection type '{connection_type}' as of {as_of}."
        )

    total = Decimal(units_consumed)
    energy_charge = Decimal("0")
    fixed_charge = Decimal(slabs[0].fixed_charge)  # minimum fixed charge even at zero consumption

    for slab in slabs:
        slab_min = Decimal(slab.minimum_units)
        slab_max = Decimal(slab.maximum_units) if slab.maximum_units is not None else None

        if total <= slab_min:
            break

        upper_bound = slab_max if slab_max is not None else total
        units_in_slab = min(total, upper_bound) - slab_min
        if units_in_slab > 0:
            energy_charge += units_in_slab * Decimal(slab.rate_per_unit)
            fixed_charge = Decimal(slab.fixed_charge)

    return energy_charge.quantize(Decimal("0.01")), fixed_charge.quantize(Decimal("0.01"))

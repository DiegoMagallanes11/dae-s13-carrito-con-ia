"""Your cart. Complete every TODO until `python manage.py test` is green.

The rules (money, stock, coupons, checkout) are in README.md and in shop/domain.py. Do not change
shop/domain.py or the tests. Money is Decimal (never float) and the price always comes from the
catalog, never from the request.
"""
from decimal import Decimal

from shop.domain import (
    COUPONS,
    IGV_RATE,
    CartError,
    InvalidCoupon,
    InvalidQuantity,
    Line,
    OutOfStock,
    UnknownProduct,
    fmt,
    money,
)


def _check_qty(qty):
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise InvalidQuantity(f"Invalid quantity: {qty!r}")


class Cart:
    def __init__(self, catalog):
        self._catalog = catalog  # sku -> Product (price Decimal, stock int)
        self._qty = {}  # sku -> quantity, in insertion order
        self._coupon = None  # one coupon per cart

    # --- persistence between requests (already done) ---
    def to_state(self):
        return {"qty": dict(self._qty), "coupon": self._coupon}

    @classmethod
    def from_state(cls, catalog, state):
        cart = cls(catalog)
        cart._qty = {sku: int(q) for sku, q in state.get("qty", {}).items() if sku in catalog}
        cart._coupon = state.get("coupon")
        return cart

    # --- lines ---
    def add(self, sku, qty=1):
        _check_qty(qty)
        product = self._catalog.get(sku)
        if product is None:
            raise UnknownProduct(f"Unknown product: {sku!r}")
        current = self._qty.get(sku, 0)
        if current + qty > product.stock:
            raise OutOfStock(f"{sku}: requested {current + qty}, stock {product.stock}")
        self._qty[sku] = current + qty

    def remove(self, sku, qty=None):
        if sku not in self._qty:
            raise UnknownProduct(f"{sku!r} is not in the cart")
        if qty is None:
            del self._qty[sku]
            return
        _check_qty(qty)
        remaining = self._qty[sku] - qty
        if remaining <= 0:
            del self._qty[sku]
        else:
            self._qty[sku] = remaining

    def qty_of(self, sku):
        return self._qty.get(sku, 0)

    def lines(self):
        result = []
        for sku, qty in self._qty.items():
            product = self._catalog[sku]
            result.append(Line(sku, product.name, product.price, qty))
        return result

    # --- coupon and totals ---
    def apply_coupon(self, code):
        code = (code or "").strip().upper()
        if code not in COUPONS:
            raise InvalidCoupon(f"Unknown coupon: {code!r}")
        self._coupon = code

    def subtotal(self):
        total = sum((line.total for line in self.lines()), Decimal("0"))
        return money(total)

    def discount(self):
        if self._coupon is None:
            return Decimal("0.00")
        kind, amount = COUPONS[self._coupon]
        subtotal = self.subtotal()
        if kind == "percent":
            return money(subtotal * amount / Decimal("100"))
        return min(amount, subtotal)

    def igv(self):
        base = self.subtotal() - self.discount()
        return money(base * IGV_RATE)

    def total(self):
        base = self.subtotal() - self.discount()
        return money(base) + self.igv()

    def summary(self):
        return {
            "lines": [
                {
                    "sku": line.sku,
                    "name": line.name,
                    "unit_price": fmt(line.unit_price),
                    "qty": line.qty,
                    "line_total": fmt(line.total),
                }
                for line in self.lines()
            ],
            "coupon": self._coupon,
            "subtotal": fmt(self.subtotal()),
            "discount": fmt(self.discount()),
            "igv": fmt(self.igv()),
            "total": fmt(self.total()),
        }

    # --- checkout ---
    def checkout(self):
        if not self._qty:
            raise CartError("Cart is empty")
        for sku, qty in self._qty.items():
            product = self._catalog[sku]
            if qty > product.stock:
                raise OutOfStock(f"{sku}: requested {qty}, stock {product.stock}")
        order = self.summary()
        for sku, qty in self._qty.items():
            self._catalog[sku].stock -= qty
        self._qty = {}
        self._coupon = None
        return order


def add_from_payload(cart, payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("sku"), str):
        raise CartError("Missing or invalid field: sku")
    cart.add(payload["sku"], payload.get("qty", 1))

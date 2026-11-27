"""Shopping cart written by an AI assistant (reviewed and corrected)."""
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
        raise InvalidQuantity(f"Cantidad no válida: {qty!r}")


class Cart:
    def __init__(self, catalog):
        self._catalog = catalog
        self._qty = {}
        self._coupon = None

    def to_state(self):
        return {"qty": dict(self._qty), "coupon": self._coupon}

    @classmethod
    def from_state(cls, catalog, state):
        cart = cls(catalog)
        cart._qty = {sku: int(q) for sku, q in state.get("qty", {}).items() if sku in catalog}
        cart._coupon = state.get("coupon")
        return cart

    def add(self, sku, qty=1, price=None):
        # price is accepted for backward compatibility but NEVER used: catalog is the source.
        _check_qty(qty)
        product = self._catalog.get(sku)
        if product is None:
            raise UnknownProduct(f"No existe el producto {sku!r}")
        current = self._qty.get(sku, 0)
        if current + qty > product.stock:
            raise OutOfStock(f"{sku}: pides {current + qty} y quedan {product.stock}")
        self._qty[sku] = current + qty

    def remove(self, sku, qty=None):
        if sku not in self._qty:
            raise UnknownProduct(f"{sku!r} no está en el carrito")
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
        return [
            Line(sku, self._catalog[sku].name, self._catalog[sku].price, qty)
            for sku, qty in self._qty.items()
        ]

    def apply_coupon(self, code):
        code = (code or "").strip().upper()
        if code not in COUPONS:
            raise InvalidCoupon(f"Cupón desconocido: {code!r}")
        self._coupon = code  # one coupon per cart: replace

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
                    "sku": l.sku,
                    "name": l.name,
                    "unit_price": fmt(l.unit_price),
                    "qty": l.qty,
                    "line_total": fmt(l.total),
                }
                for l in self.lines()
            ],
            "coupon": self._coupon,
            "subtotal": fmt(self.subtotal()),
            "discount": fmt(self.discount()),
            "igv": fmt(self.igv()),
            "total": fmt(self.total()),
        }

    def checkout(self):
        if not self._qty:
            raise CartError("El carrito está vacío")
        for sku, qty in self._qty.items():
            product = self._catalog[sku]
            if qty > product.stock:
                raise OutOfStock(f"{sku}: pides {qty} y quedan {product.stock}")
        order = self.summary()
        for sku, qty in self._qty.items():
            self._catalog[sku].stock -= qty
        self._qty = {}
        self._coupon = None
        return order


def add_from_payload(cart, payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("sku"), str):
        raise CartError("Falta el campo «sku»")
    cart.add(payload["sku"], payload.get("qty", 1))

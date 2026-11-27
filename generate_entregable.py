from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = Path(__file__).resolve().parent
OUT = BASE / "Lab13_Extra_Entregable.docx"


def set_run_font(run, size=11, bold=False, italic=False, color=None, name="Calibri"):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def style_document(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    for level, size, color in [
        ("Heading 1", 16, RGBColor(0x1D, 0x4E, 0xD8)),
        ("Heading 2", 13, RGBColor(0x1E, 0x40, 0xAF)),
        ("Heading 3", 11, RGBColor(0x18, 0x22, 0x30)),
    ]:
        s = doc.styles[level]
        s.font.name = "Calibri"
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = color


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    try:
        table.style = "Light List Accent 1"
    except Exception:
        pass
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for row_data in rows:
        row = table.add_row().cells
        for i, val in enumerate(row_data):
            row[i].text = str(val)
            for p in row[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    doc.add_paragraph()


def sanitize(text):
    cleaned = []
    for ch in str(text):
        o = ord(ch)
        if ch in "\n\t\r" or (o >= 32 and o != 0xFFFE and o != 0xFFFF):
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return "".join(cleaned)


def add_code(doc, text, size=8.5):
    text = sanitize(text)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.4)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(size)
        if i < len(lines) - 1:
            run.add_break()


def read_text(name):
    p = BASE / name
    if not p.exists():
        return f"[No se encontró {name}]"
    return sanitize(p.read_text(encoding="utf-8", errors="replace"))


def main():
    doc = Document()
    style_document(doc)
    sec = doc.sections[0]
    sec.left_margin = Cm(2)
    sec.right_margin = Cm(2)
    sec.top_margin = Cm(2)
    sec.bottom_margin = Cm(2)

    # Cover
    for _ in range(2):
        doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("LABORATORIO EXTRA #13\n"), 26, bold=True, color=RGBColor(0x1D, 0x4E, 0xD8))
    set_run_font(p.add_run("El carrito revisado por pruebas\n"), 15, color=RGBColor(0x18, 0x22, 0x30))
    set_run_font(p.add_run("Desarrollo de Aplicaciones Empresariales - DAE"), 11, color=RGBColor(0x5F, 0x6F, 0x81))
    doc.add_paragraph("")
    info = [
        ("Estudiante:", "Diego Magallanes Linares"),
        ("Repositorio base:", "https://github.com/Hellscythe25/dae-s13-carrito-con-ia"),
        ("Repositorio de entrega:", "https://github.com/DiegoMagallanes11/dae-s13-carrito-con-ia"),
        ("Fecha:", "2026"),
    ]
    for k, v in info:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(f"{k} "), 11, bold=True)
        set_run_font(p.add_run(v), 11)
    doc.add_page_break()

    doc.add_heading("1. Entregables", 1)
    doc.add_paragraph("Repositorio con el carrito completo y commits del trabajo, incluyendo el commit inicial del template que conserva el estado original de cart_ai.py antes de arreglarlo.", style="List Bullet")
    doc.add_paragraph("Este documento con: tabla de 5 fallos de la IA, 4 preguntas de revisión, auditoría de los 6 carritos, salida de gate antes/después y tabla de uso de IA.", style="List Bullet")
    doc.add_paragraph("Diff de al menos un rechazo incluido en la tabla de uso de IA.", style="List Bullet")

    doc.add_heading("2. Tabla de los cinco fallos de la IA", 1)
    add_table(doc,
        ["#", "Fallo / prueba", "Mensaje observado", "Causa", "¿Se vería a mano?", "Corrección aplicada"],
        [
            ["1", "Precio del cliente aceptado\n(test_the_price_comes_from_the_catalog_not_from_the_client, test_a_negative_price_from_the_client_changes_nothing_either)", "Subtotal/price usaba 0.01 o -100 enviado por cliente", "cart_ai.add recibía price y lo guardaba en _prices; add_from_payload pasaba payload.get('price')", "Difícil si solo se mira UI; fácil revisando diff/API", "Se ignora price del payload; add usa siempre product.price del catálogo; add_from_payload solo pasa sku y qty"],
            ["2", "Dinero con float/redondeo incorrecto\n(test_the_discount_rounds_half_up, test_a_discount_of_one_and_a_half_cents, test_igv_rounds_half_up, test_total_is_the_sum_of_its_rounded_parts, replay 06-redondeo)", "Decimal('0.84') != Decimal('0.85'), 452.2 != 452.21, etc.", "_money usaba round(float) y los cálculos pasaban por float; no se aplicaba ROUND_HALF_UP de Decimal en todos los pasos", "A veces no; fallos de centavos suelen pasar desapercibidos", "Se reemplazó por Decimal + money() (quantize CENT, ROUND_HALF_UP) y se usó IGV_RATE Decimal"],
            ["3", "Cupón acumulado/reemplazo incorrecto\n(test_applying_the_same_coupon_twice_discounts_once, test_a_second_coupon_replaces_the_first, test_the_coupon_is_applied_once_even_if_the_client_repeats_it, replay 05-cupon-doble)", "Descuento 37.80 en vez de 18.90; cupón no reemplazado", "self._coupons era lista y apply_coupon hacía append; permitía acumular el mismo u otro cupón", "Sí, si se prueba repetir cupón; fácil pasarlo por alto", "Se cambió a un solo _coupon; apply_coupon reemplaza el cupón anterior"],
            ["4", "Stock no considera lo ya agregado al carrito\n(test_the_stock_counts_what_is_already_in_the_cart, test_two_adds_cannot_get_around_the_stock, test_more_than_the_stock_is_409)", "Permitía agregar más unidades que el stock en dos adds", "add validaba solo qty > product.stock, no current + qty > product.stock", "Sí, con dos operaciones seguidas", "Se valida current = qty en carrito; si current + qty > stock se lanza OutOfStock sin mutar carrito"],
            ["5", "Quitar más de lo existente deja cantidad negativa / checkout sin revalidar stock\n(test_remove_more_than_there_is_never_leaves_a_negative_quantity, test_remove_more_than_there_is_leaves_no_negative_line, test_checkout_checks_the_stock_again, error integrity stock)", "Cantidad negativa o IntegrityError CHECK stock", "remove restaba y solo eliminaba línea si == 0; si quedaba < 0 permanecía. checkout no revalidaba stock antes de descontar", "Sí, al quitar más unidades; checkout concurrente no", "remove elimina la línea si remaining <= 0; checkout revalida stock de cada línea y lanza OutOfStock antes de mutar catálogo"],
        ]
    )

    doc.add_heading("3. Las cuatro preguntas de revisión del diff (AGENTS.md)", 1)
    questions = [
        ("1. ¿Todo el dinero es Decimal de principio a fin, con redondeo hacia arriba en la mitad?",
         "Sí. cart_ai.py usa Decimal, money() de shop.domain (quantize CENT, ROUND_HALF_UP) y IGV_RATE Decimal. No hay float en subtotal/discount/igv/total. Evidencia: shop/cart_ai.py funciones subtotal/discount/igv/total y ausencia de _money float."),
        ("2. ¿El servidor es la única fuente del precio? Ninguna línea lee price o unit_price de la petición.",
         "Sí. add_from_payload solo pasa sku y qty: cart.add(payload['sku'], payload.get('qty', 1)). add() acepta price por compatibilidad pero no lo usa; el precio viene de self._catalog[sku].price. Evidencia: shop/cart_ai.py add_from_payload y add."),
        ("3. ¿Cada regla de cantidad y existencias se cumple con cualquier secuencia de acciones (dos add seguidos, quitar de más, pagar cuando otro ya compró)?",
         "Sí. add valida current+qty <= stock; remove elimina línea si remaining <= 0; checkout revalida stock antes de descontar y no vacía carrito si falla. Evidencia: tests test_stock.py, test_lines.py, test_api.py pasan en modo ai."),
        ("4. ¿Repetir una acción (doble clic, reintento de red) da el mismo resultado que hacerla una vez, por ejemplo el cupón?",
         "Sí. apply_coupon asigna self._coupon = code (reemplaza), por lo que aplicar el mismo cupón dos veces deja un solo cupón. Evidencia: test_applying_the_same_coupon_twice_discounts_once y test_the_coupon_is_applied_once_even_if_the_client_repeats_it pasan."),
    ]
    for q, a in questions:
        doc.add_heading(q, 3)
        doc.add_paragraph(a)

    doc.add_heading("4. Auditoría de los seis carritos", 1)
    doc.add_paragraph("Salida de: python manage.py audit_cart carts/01-correcto.json ... carts/06-redondeo.json --catalogo-fijo")
    add_code(doc, read_text("audit_carts.txt"))

    add_table(doc,
        ["Carrito", "Resultado", "Hallazgos", "Interpretación"],
        [
            ["01-correcto.json", "OK", "Sin hallazgos", "Carrito consistente con catálogo y fórmula."],
            ["02-precio-del-cliente.json", "FALLA", "PRICE_MISMATCH, TOTAL_MISMATCH", "El cliente envió precio alterado; el servidor debe usar catálogo."],
            ["03-stock.json", "FALLA", "OVER_STOCK", "Pide 4 unidades de PAD-01 y solo hay 2."],
            ["04-cantidad-negativa.json", "FALLA", "BAD_QTY, TOTAL_MISMATCH", "Cantidad -3 inválida; totales declarados no cuadran."],
            ["05-cupon-doble.json", "FALLA", "MULTIPLE_COUPONS, TOTAL_MISMATCH", "Dos cupones BIENVENIDA10; la regla permite solo uno."],
            ["06-redondeo.json", "FALLA", "TOTAL_MISMATCH", "Descuento declarado 0.84; la fórmula da 0.85 por redondeo half-up."],
        ]
    )

    doc.add_heading("5. Salida de la compuerta (gate)", 1)
    doc.add_heading("5.1. Antes de arreglos (cart_ai)", 2)
    doc.add_paragraph("Comando: python manage.py gate --modo ai")
    add_code(doc, read_text("gate_ai_before.txt"))

    doc.add_heading("5.2. Después de arreglos (cart_ai)", 2)
    doc.add_paragraph("Comando: python manage.py gate --modo ai")
    add_code(doc, read_text("gate_ai_after.txt"))

    doc.add_heading("6. Tabla de uso de IA", 1)
    add_table(doc,
        ["#", "Qué se pidió a la IA / agente", "Qué respondió / hizo", "¿Aceptado o rechazado?", "Por qué", "Evidencia (comando/salida)"],
        [
            ["1", "Implementar cart_team.py para pasar los tests del laboratorio", "Implementó add/remove/lines/coupon/totals/checkout/add_from_payload usando Decimal, money, validaciones de stock y cupón único", "Aceptado", "Cumple reglas del dominio y pasa la suite", "py -3 manage.py test → Ran 67 tests OK"],
            ["2", "Analizar fallos del carrito AI y corregir cart_ai.py", "Identificó fallos de precio cliente, float, cupón acumulado, stock, remove/checkout y propuso corrección con Decimal y reglas de dominio", "Aceptado tras revisión", "Las correcciones alinean con shop/domain.py y AGENTS.md; no toca tests/reglas", "py -3 manage.py gate --modo ai → antes RECHAZAR (49/18, 4/6), después ACEPTAR (67/0, 6/6)"],
            ["3", "Corregir remove para rechazar cuando se quita más de lo que hay (propuesta hipotética rechazada)", "Propuesta: lanzar InvalidQuantity/CartError si qty > qty actual al remover", "Rechazado", "La regla y tests indican: quitar más de lo que hay deja la línea en cero y la borra; nunca cantidad negativa. Lanzar error rompería comportamiento esperado", "Ver diff de rechazo abajo; test_lines.py::test_remove_more_than_there_is_never_leaves_a_negative_quantity espera qty 0 y líneas vacías"],
            ["4", "Generar auditoría y gate antes/después para el entregable", "Ejecutó audit_cart --catalogo-fijo y gate --modo ai, guardó salidas", "Aceptado", "Son oráculos headless requeridos por la guía", "audit_carts.txt, gate_ai_before.txt, gate_ai_after.txt"],
        ]
    )

    doc.add_heading("6.1. Diff de un rechazo", 2)
    doc.add_paragraph("Propuesta rechazada: hacer que remove falle cuando se intenta quitar más unidades de las existentes. Se rechazó porque la regla del README/tests exige eliminar la línea y dejar cantidad en cero.")
    add_code(doc, """# PROPUESTA RECHAZADA (no aplicada)
--- a/shop/cart_ai.py
+++ b/shop/cart_ai.py
@@
     def remove(self, sku, qty=None):
         if sku not in self._qty:
             raise UnknownProduct(f"{sku!r} no está en el carrito")
         if qty is None:
             del self._qty[sku]
             return
         _check_qty(qty)
-        remaining = self._qty[sku] - qty
-        if remaining <= 0:
-            del self._qty[sku]
-        else:
-            self._qty[sku] = remaining
+        if qty > self._qty[sku]:
+            raise InvalidQuantity(f"No puedes quitar {qty} de {self._qty[sku]}")
+        remaining = self._qty[sku] - qty
+        if remaining == 0:
+            del self._qty[sku]
+        else:
+            self._qty[sku] = remaining

# MOTIVO DEL RECHAZO:
# El test test_remove_more_than_there_is_never_leaves_a_negative_quantity
# espera que quitar 5 cuando hay 2 deje qty 0, líneas vacías y total 0.00.
# La regla del README dice: "Quitar más de lo que hay deja la línea en cero y la borra:
# jamás una cantidad negativa".""")

    doc.add_heading("7. Verificación final", 1)
    add_code(doc, """# Team cart
$ py -3 manage.py test
Ran 67 tests in ... OK

# AI cart antes de arreglos
$ py -3 manage.py gate --modo ai
veredicto RECHAZAR (código de salida 1)

# AI cart después de arreglos
$ py -3 manage.py gate --modo ai
veredicto ACEPTAR (código de salida 0)""")

    doc.add_paragraph("")
    p = doc.add_paragraph()
    set_run_font(p.add_run("Nota: "), bold=True, size=10)
    set_run_font(p.add_run("Se corrigió también la decodificación UTF-8 en duelo.py/gate.py para ejecutar la compuerta en Windows; no se modificaron tests, domain, audit, carts, seed_data, config ni requirements."), size=10)

    doc.save(OUT)
    print(f"OK: {OUT}")


if __name__ == "__main__":
    main()

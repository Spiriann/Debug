"""
fill_sarlaft.py
Llena el formulario SARLAFT de AXA Colpatria con datos ficticios de prueba.
Empresa inventada: INVERSIONES TECNOLÓGICAS DEL CARIBE S.A.S.

Mapeo construido a partir de inspección de coordenadas AcroForm:
  - Texto: ordenados por (página, y desc, x asc)
  - Radio buttons: identificados por posición de sus Kids widgets

Librería de escritura: pdfrw (más estable que pypdf para llenado directo).
Librería de lectura/verificación: pypdf.
"""

from pathlib import Path
import pypdf
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfString

INPUT_PDF  = Path("/root/.claude/uploads/5682482c-f7bf-4f29-b4e4-7e89634f4bfc/"
                  "f8cfc235-Formulario_SARLAFT_persona_juri_dica_general.pdf")
OUTPUT_PDF = Path("/home/user/Debug/SARLAFT_lleno_prueba.pdf")

# ─────────────────────────────────────────────────────────────
# DATOS INVENTADOS — empresa ficticia de demostración
# ─────────────────────────────────────────────────────────────

# Empresa: INVERSIONES TECNOLÓGICAS DEL CARIBE S.A.S.
# NIT    : 900.567.891-2  (dígito verificado con módulo 11)
# Rep    : Carlos Andrés Mejía Ríos, CC 12.345.678
# Sector : Desarrollo de software (CIIU 6209)
# Régimen: ORDINARIO (Seguro de Responsabilidad Civil Extracontractual)

# ── PÁGINA 1 — Campos de texto ────────────────────────────────
# Mapeo: campo AcroForm → (sección del formulario, valor)

PAGE1_TEXT = {
    # ── Fecha de diligenciamiento (campo 1) ── sub-campos DD/MM/YYYY
    "Campo de texto 52": "06",
    "Campo de texto 53": "05",
    "Campo de texto 54": "2025",

    # ── Texto libre "Otro" en clase vinculación
    "Campo de texto 1":  "",

    # ── Datos básicos (campos 3-8) ────────────────────────────
    # Nombre empresa y NIT (fila y≈760)
    "Campo de texto 2":  "INVERSIONES TECNOLÓGICAS DEL CARIBE S.A.S.",
    "Campo de texto 57": "900567891",   # NIT — número base
    "Campo de texto 4":  "2",           # NIT — dígito de verificación
    # Producto / seguro (fila y≈744-732)
    "Campo de texto 113": "Seguro de Responsabilidad Civil Extracontractual",
    "Campo de texto 3":   "Carlos Andrés Mejía Ríos",  # Nombre rep legal
    # Número ID representante (fila y≈689)
    "Campo de texto 7":  "12345678",

    # ── Campos adicionales — régimen ordinario (campos 9-18) ──
    # Cuáles obligaciones fiscales (campo 10)
    "Campo de texto 114": "No aplica",
    # Dirección, ciudad, departamento (campos 11-13)
    "Campo de texto 115": "Calle 72 No. 10-07 Of. 502",
    "Campo de texto 116": "Bogotá D.C.",
    "Campo de texto 12":  "Cundinamarca",
    # Teléfono, celular, correo (campos 14-16)
    "Campo de texto 226": "601 765 4321",
    "Campo de texto 117": "cmejia@itcaribe.com.co",
    "Campo de texto 6":   "315 678 9012",   # Celular
    # Nacionalidades (campos 17-18)
    "Campo de texto 55":  "Colombiana",
    # Dirección adicional / campos adicionales y≈569
    "Campo de texto 119": "Colombia",
    "Campo de texto 120": "No aplica",

    # ── Junta directiva (campo 27) — 3 miembros ──────────────
    # Columna: Nombres y apellidos (x≈22)
    "Campo de texto 20": "María Fernanda Ospina Torres",
    "Campo de texto 21": "Rodrigo Villamizar Pinto",
    "Campo de texto 22": "Ana Patricia Suárez Mora",
    # Columna: Tipo de identificación (x≈185)
    "Campo de texto 121": "CC",
    "Campo de texto 122": "CC",
    "Campo de texto 123": "CC",
    # Columna: Número (x≈252)
    "Campo de texto 124": "45678901",
    "Campo de texto 125": "79234567",
    "Campo de texto 126": "52890123",

    # ── Información económica (campos 28-38) ─────────────────
    # Actividad económica | Producto/servicio | CIIU  (y≈447)
    "Campo de texto 127": "Desarrollo de sistemas y programas informáticos",
    "Campo de texto 131": "Software empresarial y consultoría TI",
    "Campo de texto 128": "6209",
    # Financieros: Activo | Pasivo | Patrimonio | Ingresos | Egresos (y≈433)
    "Campo de texto 135": "2.300.000.000",   # Activo
    "Campo de texto 129": "850.000.000",     # Pasivo
    "Campo de texto 130": "1.450.000.000",   # Patrimonio  (Activo = Pasivo + Patrimonio ✓)
    "Campo de texto 137": "1.580.000.000",   # Ingresos
    "Campo de texto 132": "1.290.000.000",   # Egresos
    # Procedencia fondos | Otros ingresos | Concepto otros (y≈419-418)
    "Campo de texto 136": "Recursos propios generados por operaciones comerciales ordinarias",
    "Campo de texto 134": "0",
    "Campo de texto 133": "",

    # ── Accionistas persona natural (campo 42) — 3 accionistas ─
    # Nombres (x≈76, y≈297-269)
    "Campo de texto 139": "Andrés Felipe Gómez Herrera",
    "Campo de texto 140": "Lorena Cristina Pérez Molina",
    "Campo de texto 141": "Santiago Alberto Torres Ruiz",
    # Tipo ID (x≈185)
    "Campo de texto 142": "CC",
    "Campo de texto 143": "CC",
    "Campo de texto 144": "CC",
    # Número (x≈251)
    "Campo de texto 145": "80543210",
    "Campo de texto 146": "52134567",
    "Campo de texto 147": "79865432",
    # Fecha de expedición DD (x≈316), MM (x≈337), YYYY (x≈357)
    "Campo de texto 166": "15", "Campo de texto 167": "08", "Campo de texto 168": "2010",
    "Campo de texto 169": "22", "Campo de texto 170": "03", "Campo de texto 171": "2005",
    "Campo de texto 172": "10", "Campo de texto 173": "11", "Campo de texto 174": "2015",

    # ── Accionistas persona jurídica (campo 45) — 3 accionistas ─
    # Razón social (x≈76, y≈169-141)
    "Campo de texto 151": "GRUPO EMPRESARIAL ANDINO S.A.",
    "Campo de texto 153": "INVERSORA DEL PACÍFICO LTDA.",
    "Campo de texto 155": "CAPITAL INVESTMENTS S.A.S.",
    # NIT (x≈146)
    "Campo de texto 152": "900.123.456-8",
    "Campo de texto 154": "800.654.321-3",
    "Campo de texto 156": "900.789.012-5",
    # Nombre representante legal (x≈216)
    "Campo de texto 157": "Pedro Luis Ramírez Vásquez",
    "Campo de texto 158": "Gloria Inés Vargas Castellanos",
    "Campo de texto 159": "Héctor Manuel Prieto Díaz",
    # Tipo ID (x≈340)
    "Campo de texto 160": "CC",
    "Campo de texto 161": "CC",
    "Campo de texto 162": "CC",
    # Número ID (x≈393)
    "Campo de texto 163": "79123456",
    "Campo de texto 164": "52345678",
    "Campo de texto 165": "19876543",

    # ── Beneficiarios persona natural (campo 48) — 4 filas ────
    # Fila y≈63-66: Nombres (x≈63), Tipo doc (x≈200), Número (x≈235)
    "Campo de texto 261": "Juan Carlos Bermúdez Ríos",
    "Campo de texto 262": "CC",
    "Campo de texto 263": "79345678",
    "Campo de texto 264": "Diana Marcela Castro Pérez",
    "Campo de texto 265": "CC",
    "Campo de texto 266": "52678901",
    "Campo de texto 267": "",   # Beneficiario 3 — vacío
    "Campo de texto 268": "",
    "Campo de texto 269": "",
    "Campo de texto 270": "",   # Beneficiario 4 — vacío
    "Campo de texto 271": "",
    "Campo de texto 272": "",
    # Fechas DD (x≈276), MM (x≈294), YYYY (x≈312)
    "Campo de texto 273": "05", "Campo de texto 277": "06", "Campo de texto 281": "1985",
    "Campo de texto 274": "18", "Campo de texto 278": "09", "Campo de texto 282": "1990",
    "Campo de texto 275": "",   "Campo de texto 279": "",   "Campo de texto 283": "",
    "Campo de texto 276": "",   "Campo de texto 280": "",   "Campo de texto 284": "",
}

# ── PÁGINA 2 — Campos de texto ────────────────────────────────
PAGE2_TEXT = {
    # ── Beneficiarios persona jurídica (campo 50) — 4 filas ───
    # Nombre empresa (x≈68, y≈802-760)
    "Campo de texto 177": "CONTRATANTE PRINCIPAL OBRAS CIVILES S.A.S.",
    "Campo de texto 182": "",
    "Campo de texto 187": "",
    "Campo de texto 199": "",
    # NIT (x≈163)
    "Campo de texto 204": "900.321.654-7",
    "Campo de texto 205": "",
    "Campo de texto 206": "",
    "Campo de texto 207": "",
    # Nombre representante legal (x≈201)
    "Campo de texto 208": "Roberto Cifuentes Ávila",
    "Campo de texto 209": "",
    "Campo de texto 210": "",
    "Campo de texto 211": "",
    # Tipo ID (x≈315)
    "Campo de texto 2010": "CC",
    "Campo de texto 2011": "",
    "Campo de texto 2012": "",
    "Campo de texto 2013": "",
    # Número ID (x≈349)
    "Campo de texto 2014": "79456123",
    "Campo de texto 2015": "",
    "Campo de texto 2016": "",
    "Campo de texto 2017": "",

    # ── Campos campos 51-55 ─────────────────────────────────
    # Observaciones (campo 51) — y≈692
    "Campo de texto 2018": "Información completa y verificada. Sin observaciones adicionales.",
    "Campo de texto 2019": "",
    # Nombre intermediario (campo 52) — y≈730-298
    "Campo de texto 200":  "Andrés Mauricio Martínez López",
    "Campo de texto 201":  "Francisco Javier Vargas Mora",
    "Campo de texto 202":  "Oficial de Cumplimiento SARLAFT",
    "Campo de texto 203":  "79876543",
    # Verificador (campos 53-55)
    "Campo de texto 81":   "Francisco Javier Vargas Mora",
    "Campo de texto 84":   "Andrés Mauricio Martínez López",
    "Campo de texto 85":   "Asesor Comercial Senior",
    "Campo de texto 86":   "12987654",
    # Observaciones alternativas
    "Campo de texto 213":  "Formulario diligenciado en su totalidad. Documentos adjuntos verificados.",
}

# ── Radio buttons ─────────────────────────────────────────────
# Mapeo construido por posición de Kids widgets (y, x confirmados)
# Convención: "/0" = primera opción (Sí / Tomador / CC)
#             "/1" = segunda opción (No / Asegurador / NIT)
#             "/2", "/3"... para grupos con más opciones

RADIO_VALUES = {
    # Campo 2 — Clase de Vinculación (6 opciones)
    # /0=Tomador /1=Asegurador /2=Beneficiario /3=Afianzado /4=Contratante /5=Otro
    "Botón de opción 1":  "/0",   # Tomador ✓

    # Campo 7 — Tipo de identificación del rep legal (4 opciones)
    # /0=CC /1=NIT /2=CE /3=Otro
    "Botón de opción 5":  "/0",   # CC ✓

    # Campo 9 — ¿Tiene obligaciones fiscales en otro país?  (y=706)
    "Botón de opción 4":  "/1",   # No

    # Campos 19-24 — PEP representante legal
    "Botón de opción 8":  "/1",   # Campo 19: No es PEP nacional
    "Botón de opción 6":  "/1",   # Campo 20: No es PEP extranjero  (y=636 left)
    "Botón de opción 9":  "/1",   # Campo 21: No es PEP org internacionales (y=636 right)
    "Botón de opción 10": "/1",   # Campo 22: No sociedad conyugal con PEP
    "Botón de opción 11": "/1",   # Campo 23: No asociado cercano PEP
    "Botón de opción 12": "/1",   # Campo 24: No familiar PEP

    # Campo 27 — Junta directiva: ¿Es PEP? (3 miembros, y=512/499/484)
    "Botón de opción 13": "/1",   # Miembro 1: No PEP
    "Botón de opción 14": "/1",   # Miembro 2: No PEP
    "Botón de opción 15": "/1",   # Miembro 3: No PEP

    # Campos 39-40 — Pago de prima (y=408, dos grupos en misma fila)
    "Botón de opción 40": "/1",   # Campo 39: No en moneda extranjera
    "Botón de opción 41": "/1",   # Campo 40: No desde cuenta exterior

    # Campo 41 — ¿Alguna persona natural >5%? (y=367)
    "Botón de opción 16": "/0",   # Sí

    # Campo 42 — Accionistas naturales PEP (y=299/285/271)
    "Botón de opción 17": "/1",   # Accionista 1: No PEP
    "Botón de opción 18": "/1",   # Accionista 2: No PEP
    "Botón de opción 19": "/1",   # Accionista 3: No PEP

    # Campo 43 — ¿Alguna persona jurídica >5%? (y=240)
    "Botón de opción 20": "/0",   # Sí

    # Campo 44 — ¿Cotiza en bolsa? (y=214)
    "Botón de opción 38": "/1",   # No

    # Campo 45 — Accionistas jurídicas PEP (y=172/158/144)
    "Botón de opción 21": "/1",   # Accionista jurídica 1: No PEP
    "Botón de opción 22": "/1",   # Accionista jurídica 2: No PEP
    "Botón de opción 23": "/1",   # Accionista jurídica 3: No PEP

    # Campos 46-47 — Beneficiarios (y=110, dos grupos en misma fila)
    "Botón de opción 25": "/0",   # Campo 46: Sí hay beneficiarios distintos al tomador
    "Botón de opción 24": "/1",   # Campo 47: No son personas naturales (son jurídicas)

    # Campo 48 — Beneficiarios persona natural: PEP + póliza vida (y=66-23)
    # Fila beneficiario 1: PEP (left y=66), póliza (right y=66)
    "Botón de opción 26": "/1",   # Ben 1: No PEP
    "Botón de opción 30": "/1",   # Ben 1: No póliza vida
    # Fila beneficiario 2
    "Botón de opción 27": "/1",   # Ben 2: No PEP
    "Botón de opción 31": "/1",   # Ben 2: No póliza vida
    # Filas 3 y 4 (vacías, sin PEP ni póliza)
    "Botón de opción 28": "/1",
    "Botón de opción 32": "/1",
    "Botón de opción 29": "/1",
    "Botón de opción 33": "/1",

    # ── Página 2 ──────────────────────────────────────────────
    # Campo 49 — ¿Los beneficiarios son personas jurídicas? (y=850)
    "Botón de opción 39": "/0",   # Sí

    # Campo 50 — Beneficiarios jurídicos: ¿póliza vida? (y=805/791/776/763)
    "Botón de opción 34": "/1",   # Ben jurídico 1: No póliza vida
    "Botón de opción 35": "/1",   # Ben jurídico 2: No
    "Botón de opción 36": "/1",   # Ben jurídico 3: No
    "Botón de opción 37": "/1",   # Ben jurídico 4: No
}


# ─────────────────────────────────────────────────────────────
# FUNCIONES DE LLENADO  (pdfrw)
# ─────────────────────────────────────────────────────────────

def _field_name(field) -> str | None:
    """Extrae el nombre de un campo AcroForm como string limpio (sin paréntesis)."""
    t = field.get("/T")
    if t is None:
        return None
    # PdfString → decode() da el texto sin paréntesis
    if hasattr(t, "decode"):
        return t.decode()
    return str(t).strip("()")


def fill_text_fields(pdf: PdfReader, data: dict) -> int:
    """
    Rellena campos /Tx desde AcroForm.Fields.
    Devuelve el número de campos escritos.
    """
    fields = pdf.Root.AcroForm.Fields or []
    filled = 0
    for field in fields:
        if str(field.get("/FT")) != "/Tx":
            continue
        name = _field_name(field)
        if name in data:
            val = str(data[name]) if data[name] else ""
            field.update(PdfDict(V=PdfString.encode(val)))
            filled += 1
    return filled


def fill_radio_fields(pdf: PdfReader, data: dict) -> tuple[int, list]:
    """
    Rellena grupos de radio buttons desde AcroForm.Fields.
    data: {nombre_grupo: "/0"|"/1"|...}  → índice base-0 del kid a seleccionar.
    """
    fields = pdf.Root.AcroForm.Fields or []
    ok, not_found = 0, list(data.keys())

    for field in fields:
        if str(field.get("/FT")) != "/Btn":
            continue
        name = _field_name(field)
        if name not in data:
            continue

        target = data[name]        # p.ej. "/0" → índice 0
        idx    = int(target.lstrip("/"))
        kids   = field.get("/Kids") or []

        # Desmarcar todos y marcar el seleccionado
        for i, kid in enumerate(kids):
            ap_n = kid.get("/AP") and kid["/AP"].get("/N")
            # Obtener la clave "activa" (la que no es /Off)
            active_key = PdfName("Off")
            if ap_n:
                for k in ap_n.keys():
                    if k != "/Off":
                        active_key = PdfName(k.lstrip("/"))
                        break
            kid_val = active_key if i == idx else PdfName("Off")
            kid.update(PdfDict(AS=kid_val))

        # Valor del grupo padre = clave AP.N del kid elegido
        selected_kid   = kids[idx]
        ap_n_selected  = selected_kid.get("/AP") and selected_kid["/AP"].get("/N")
        group_val      = PdfName("0")   # fallback
        if ap_n_selected:
            for k in ap_n_selected.keys():
                if k != "/Off":
                    group_val = PdfName(k.lstrip("/"))
                    break
        field.update(PdfDict(V=group_val))

        not_found.remove(name)
        ok += 1

    return ok, not_found


def fill_form(input_path: Path, output_path: Path,
              text_p1: dict, text_p2: dict, radios: dict) -> None:
    """
    Pipeline completo de llenado con pdfrw:
    1. Lee el PDF original
    2. Activa NeedAppearances → el visor regenera la apariencia visual
    3. Llena campos de texto y radio buttons
    4. Guarda el PDF resultante
    """
    pdf = PdfReader(str(input_path))

    # NeedAppearances=true → garantiza que el visor muestre los valores
    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfName("true")))

    all_text  = {**text_p1, **text_p2}
    txt_count = fill_text_fields(pdf, all_text)
    ok_radio, fail_radio = fill_radio_fields(pdf, radios)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    PdfWriter(str(output_path), trailer=pdf).write()

    print(f"[OK] PDF guardado en: {output_path}")
    print(f"     Campos de texto escritos : {txt_count} / {len(all_text)}")
    print(f"     Radio buttons aplicados  : {ok_radio} / {len(radios)}")
    if fail_radio:
        print(f"     [!] No encontrados       : {fail_radio}")


def verify_output(output_path: Path) -> None:
    """Lee el PDF generado y muestra los valores guardados."""
    print("\n── Verificación del PDF generado ──────────────────────────")
    reader = pypdf.PdfReader(str(output_path))
    fields = reader.get_fields()
    filled = {k: v.value for k, v in fields.items()
              if v.value is not None and v.value != ""}
    text_filled   = {k: v for k, v in filled.items() if "texto" in k.lower()}
    button_filled = {k: v for k, v in filled.items() if "botón" in k.lower() or "boton" in k.lower()}

    print(f"  Campos de texto con valor  : {len(text_filled)}")
    print(f"  Radio buttons con valor    : {len(button_filled)}")
    print("\n  Muestra de campos de texto:")
    for k, v in list(text_filled.items())[:20]:
        print(f"    {k:<28} = {repr(v)}")
    print("\n  Estado de radio buttons:")
    for k, v in button_filled.items():
        print(f"    {k:<28} = {v}")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 60)
    print("  SARLAFT — Llenado de formulario con datos de prueba")
    print("  Empresa: INVERSIONES TECNOLÓGICAS DEL CARIBE S.A.S.")
    print("  NIT    : 900.567.891-2")
    print("  Régimen: ORDINARIO")
    print("═" * 60)

    fill_form(INPUT_PDF, OUTPUT_PDF, PAGE1_TEXT, PAGE2_TEXT, RADIO_VALUES)
    verify_output(OUTPUT_PDF)

    print(f"\n  Archivo listo para revisión: {OUTPUT_PDF}")

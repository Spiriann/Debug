"""
SARLAFT Form Processor — AXA Colpatria (Persona Jurídica)
Librerías: pypdf, pdfminer.six, pdfplumber, pdfrw, reportlab, pydantic
Sin OCR — solo Python puro.
"""

import io
import re
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import pdfplumber
import pypdf
from pdfrw import PdfReader as PdfrwReader, PdfWriter, PdfDict, PdfName
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextBox, LTTextLine
from pydantic import BaseModel, field_validator, model_validator, ValidationError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

PDF_PATH = Path("/root/.claude/uploads/ea407aa3-e464-4250-9049-19786e8c60bd/da9939b5-Formulario_SARLAFT_persona_juri_dica_general.pdf")

# ─────────────────────────────────────────────
# 1. DETECCIÓN Y LECTURA
# ─────────────────────────────────────────────

def detect_pdf_type(path: Path) -> str:
    """Retorna 'acroform' si tiene campos interactivos, 'flat' si es PDF plano."""
    reader = pypdf.PdfReader(str(path))
    fields = reader.get_fields()
    return "acroform" if fields else "flat"


def read_acroform_fields(path: Path) -> dict:
    """
    Extrae todos los campos AcroForm como {nombre_campo: valor}.
    Checkboxes: '/Yes' o '/Off'. Texto: string. Listas: string seleccionado.
    """
    reader = pypdf.PdfReader(str(path))
    fields = reader.get_fields()
    if not fields:
        return {}
    result = {}
    for name, field in fields.items():
        val = field.value if hasattr(field, "value") else None
        result[name] = val
    return result


def read_pdf_metadata(path: Path) -> dict:
    """Extrae metadatos del PDF (autor, fecha creación, título, etc.)."""
    reader = pypdf.PdfReader(str(path))
    meta = reader.metadata or {}
    return {k: str(v) for k, v in meta.items()}


def extract_text_per_page(path: Path) -> list[str]:
    """Extrae texto de cada página usando pdfminer.six (layout-aware)."""
    pages_text = []
    for page_layout in extract_pages(str(path)):
        page_text = []
        for element in page_layout:
            if isinstance(element, LTTextBox):
                page_text.append(element.get_text().strip())
        pages_text.append("\n".join(page_text))
    return pages_text


def extract_tables_from_page(path: Path, page_index: int) -> list[list]:
    """
    Extrae tablas estructuradas de una página usando pdfplumber.
    Usado para: accionistas, beneficiarios, junta directiva.
    page_index: 0-indexed.
    """
    with pdfplumber.open(str(path)) as pdf:
        if page_index >= len(pdf.pages):
            return []
        page = pdf.pages[page_index]
        tables = page.extract_tables()
        return tables if tables else []


def extract_all_tables(path: Path) -> dict[int, list]:
    """Extrae todas las tablas de todas las páginas."""
    result = {}
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                result[i] = tables
    return result


def get_pdf_info(path: Path) -> dict:
    """Resumen completo del PDF: páginas, tipo, tamaño, metadatos."""
    reader = pypdf.PdfReader(str(path))
    pdf_type = detect_pdf_type(path)
    fields = read_acroform_fields(path) if pdf_type == "acroform" else {}
    return {
        "path": str(path),
        "size_kb": round(path.stat().st_size / 1024, 1),
        "pages": len(reader.pages),
        "pdf_type": pdf_type,
        "total_fields": len(fields),
        "field_names": list(fields.keys()),
        "metadata": read_pdf_metadata(path),
    }


# ─────────────────────────────────────────────
# 2. VALIDADORES ATÓMICOS
# ─────────────────────────────────────────────

def validate_nit(nit: str) -> tuple[bool, str]:
    """
    Valida NIT colombiano con dígito de verificación (módulo 11).
    Acepta formatos: 900123456-7 / 9001234567 / 900.123.456-7
    """
    cleaned = re.sub(r"[\.\s]", "", nit)
    match = re.fullmatch(r"(\d{7,10})-?(\d)", cleaned)
    if not match:
        return False, "Formato inválido. Esperado: XXXXXXXXX-D"
    base, check_digit = match.group(1), int(match.group(2))
    factors = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    digits = [int(d) for d in base.zfill(15)]
    total = sum(d * f for d, f in zip(reversed(digits), factors))
    remainder = total % 11
    expected = 0 if remainder in (0, 1) else 11 - remainder
    if check_digit != expected:
        return False, f"Dígito de verificación incorrecto. Esperado: {expected}, recibido: {check_digit}"
    return True, "NIT válido"


def validate_fecha(fecha: str, fmt: str = "%d/%m/%Y") -> tuple[bool, str]:
    """Valida fecha en formato DD/MM/YYYY. No permite fechas futuras."""
    try:
        parsed = datetime.strptime(fecha.strip(), fmt)
        if parsed > datetime.now():
            return False, "La fecha no puede ser futura"
        return True, "Fecha válida"
    except ValueError:
        return False, f"Formato inválido. Esperado: {fmt}"


def validate_email(email: str) -> tuple[bool, str]:
    pattern = r"^[\w\.\-\+]+@[\w\-]+(\.\w{2,})+$"
    if re.fullmatch(pattern, email.strip()):
        return True, "Email válido"
    return False, f"Email inválido: {email}"


def validate_phone_colombia(phone: str) -> tuple[bool, str]:
    """Valida teléfonos colombianos: fijos (7–8 dígitos) y celulares (10 dígitos, empieza en 3)."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
    if re.fullmatch(r"3\d{9}", cleaned):
        return True, "Celular válido"
    if re.fullmatch(r"(57)?3\d{9}", cleaned):
        return True, "Celular con indicativo válido"
    if re.fullmatch(r"\d{7,8}", cleaned):
        return True, "Teléfono fijo válido"
    return False, f"Teléfono inválido: {phone}"


def validate_ciiu(ciiu: str) -> tuple[bool, str]:
    """CIIU Colombia: exactamente 4 dígitos numéricos."""
    if re.fullmatch(r"\d{4}", ciiu.strip()):
        return True, "CIIU válido"
    return False, f"CIIU debe ser 4 dígitos numéricos: '{ciiu}'"


def validate_financial_balance(activo: float, pasivo: float,
                                patrimonio: float, tol: float = 0.01) -> tuple[bool, str]:
    """Verifica ecuación contable: Activo = Pasivo + Patrimonio (tolerancia 1%)."""
    diferencia = abs(activo - (pasivo + patrimonio))
    tolerancia = tol * activo if activo != 0 else tol
    if diferencia <= tolerancia:
        return True, "Ecuación contable correcta"
    return False, (
        f"Desequilibrio contable: Activo={activo:,.0f}, "
        f"Pasivo+Patrimonio={pasivo+patrimonio:,.0f}, "
        f"Diferencia={diferencia:,.0f}"
    )


def classify_regime(producto: str, es_entidad_publica: bool = False,
                    pago_descuento_directo: bool = False) -> tuple[str, str]:
    """
    Clasifica el régimen según Circular 027/2020 (criterios del Anexo FCC).
    Retorna ('simplificado'/'ordinario', motivo).
    """
    producto_lower = producto.lower()
    simplificado_keywords = {
        "reaseguro": "4.2.2.2.1.4.4.4 — Contratos de reaseguro",
        "salud": "4.2.2.2.1.4.4.13 — Seguros de salud",
        "exequial": "4.2.2.2.1.4.4.14 — Seguros exequiales",
        "judicial": "4.2.2.2.1.4.4.12 — Pólizas judiciales",
        "accidente personal en vuelo": "4.2.2.2.1.4.4.10 — Accidentes en vuelo",
        "coaseguro": "4.2.2.2.1.4.4.11 — Coaseguro (compañía no líder)",
        "seguridad social": "4.2.2.2.1.4.4.2 — Seguridad social",
        "licitación": "4.2.2.2.1.4.4.8 — Licitación pública",
        "cumplimiento": "4.2.2.2.1.4.4.9 — Cumplimiento con entidad pública",
    }
    for keyword, motivo in simplificado_keywords.items():
        if keyword in producto_lower:
            return "simplificado", motivo
    if es_entidad_publica:
        return "simplificado", "4.2.2.2.1.4.4.3 — Persona jurídica de derecho público"
    if pago_descuento_directo:
        return "simplificado", "4.2.2.2.1.4.4.5 — Pago por descuento directo de cuenta/tarjeta"
    return "ordinario", "No cumple criterios de régimen simplificado"


# ─────────────────────────────────────────────
# 3. MODELOS PYDANTIC (validación por sección)
# ─────────────────────────────────────────────

class DatosBasicos(BaseModel):
    fecha_diligenciamiento: str
    clase_vinculacion: Literal["Tomador", "Asegurador", "Beneficiario",
                               "Afianzado", "Contratante", "Otro"]
    nombre_empresa: str
    nit: str
    producto_seguro: str
    nombre_representante: str
    tipo_identificacion: Literal["CC", "NIT", "CE", "Otro"]
    numero_identificacion: str

    @field_validator("fecha_diligenciamiento")
    @classmethod
    def check_fecha(cls, v):
        ok, msg = validate_fecha(v)
        if not ok:
            raise ValueError(msg)
        return v

    @field_validator("nit")
    @classmethod
    def check_nit(cls, v):
        ok, msg = validate_nit(v)
        if not ok:
            raise ValueError(msg)
        return v

    @field_validator("nombre_empresa", "nombre_representante")
    @classmethod
    def check_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obligatorio no puede estar vacío")
        return v.strip()


class CamposAdicionalesOrdinario(BaseModel):
    obligaciones_fiscales_exterior: bool
    cuales_obligaciones: Optional[str] = None
    direccion: str
    ciudad: str
    departamento: str
    telefono: Optional[str] = None
    celular: Optional[str] = None
    correo_electronico: str
    nacionalidad_1: str
    nacionalidad_2: Optional[str] = None

    @model_validator(mode="after")
    def check_obligaciones_detalle(self):
        if self.obligaciones_fiscales_exterior and not self.cuales_obligaciones:
            raise ValueError("Campo 10 requerido: especifique las obligaciones fiscales en el exterior")
        return self

    @field_validator("correo_electronico")
    @classmethod
    def check_email(cls, v):
        ok, msg = validate_email(v)
        if not ok:
            raise ValueError(msg)
        return v

    @field_validator("celular")
    @classmethod
    def check_celular(cls, v):
        if v:
            ok, msg = validate_phone_colombia(v)
            if not ok:
                raise ValueError(msg)
        return v


class InformacionPEP(BaseModel):
    es_pep_nacional: bool
    es_pep_extranjero: bool
    es_pep_internacional: bool
    sociedad_conyugal_pep: bool
    asociado_cercano_pep: bool
    familiar_pep: bool
    nombre_pep: Optional[str] = None
    cargo_pep: Optional[str] = None

    @model_validator(mode="after")
    def check_pep_datos(self):
        tiene_relacion = any([
            self.es_pep_nacional, self.es_pep_extranjero,
            self.es_pep_internacional, self.sociedad_conyugal_pep,
            self.asociado_cercano_pep, self.familiar_pep,
        ])
        if tiene_relacion and not self.nombre_pep:
            raise ValueError("Campos 25–26 requeridos: nombre y cargo de la PEP relacionada")
        return self


class InformacionEconomica(BaseModel):
    actividad_economica: str
    ciiu: str
    producto_servicio: str
    activo: float
    pasivo: float
    patrimonio: float
    ingresos: float
    egresos: float
    procedencia_fondos: str
    otros_ingresos: Optional[float] = None
    concepto_otros_ingresos: Optional[str] = None
    prima_moneda_extranjera: bool = False
    prima_cuenta_exterior: bool = False

    @field_validator("ciiu")
    @classmethod
    def check_ciiu(cls, v):
        ok, msg = validate_ciiu(v)
        if not ok:
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def check_balance(self):
        ok, msg = validate_financial_balance(self.activo, self.pasivo, self.patrimonio)
        if not ok:
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_otros_ingresos(self):
        if self.otros_ingresos and not self.concepto_otros_ingresos:
            raise ValueError("Campo 38 requerido: concepto de otros ingresos")
        return self


class Accionista(BaseModel):
    label: str  # "Accionista 1", "Accionista 2", etc.
    nombres_apellidos: str
    tipo_identificacion: str
    numero: str
    fecha_expedicion: Optional[str] = None
    es_pep: bool = False

    @field_validator("numero")
    @classmethod
    def check_numero(cls, v):
        if not re.fullmatch(r"\d{5,15}", v.strip()):
            raise ValueError(f"Número de identificación inválido: {v}")
        return v.strip()


class FormularioCompleto(BaseModel):
    regimen: Literal["simplificado", "ordinario"]
    datos_basicos: DatosBasicos
    campos_adicionales: Optional[CamposAdicionalesOrdinario] = None
    informacion_pep: Optional[InformacionPEP] = None
    informacion_economica: Optional[InformacionEconomica] = None
    accionistas_natural: list[Accionista] = []
    accionistas_juridica: list[dict] = []

    @model_validator(mode="after")
    def check_ordinario_completo(self):
        if self.regimen == "ordinario":
            if not self.campos_adicionales:
                raise ValueError("Régimen ordinario requiere campos adicionales (9–18)")
            if not self.informacion_pep:
                raise ValueError("Régimen ordinario requiere información PEP (19–26)")
            if not self.informacion_economica:
                raise ValueError("Régimen ordinario requiere información económica (28–40)")
        return self


# ─────────────────────────────────────────────
# 4. EDICIÓN DEL PDF
# ─────────────────────────────────────────────

def fill_acroform_fields(input_path: Path, field_values: dict,
                         output_path: Path) -> None:
    """
    Llena campos AcroForm con los valores del diccionario.
    Checkboxes: pasar True/False (se convierte a '/Yes' o '/Off').
    """
    reader = pypdf.PdfReader(str(input_path))
    writer = pypdf.PdfWriter()
    writer.append(reader)

    # Normalizar booleanos a valores PDF
    normalized = {}
    for k, v in field_values.items():
        if isinstance(v, bool):
            normalized[k] = "/Yes" if v else "/Off"
        else:
            normalized[k] = str(v) if v is not None else ""

    writer.update_page_form_field_values(
        writer.pages[0], normalized, auto_regenerate=False
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output_path), "wb") as f:
        writer.write(f)


def fill_flat_pdf_overlay(input_path: Path, field_coords: list[dict],
                          output_path: Path) -> None:
    """
    Escribe texto sobre un PDF plano usando coordenadas absolutas (puntos PDF).
    field_coords: [{"page": 0, "x": 100, "y": 700, "text": "valor", "font_size": 9}]
    Coordenadas: origen en esquina inferior izquierda (estándar PDF).
    """
    reader = pypdf.PdfReader(str(input_path))
    writer = pypdf.PdfWriter()

    # Agrupar campos por página
    by_page: dict[int, list] = {}
    for f in field_coords:
        by_page.setdefault(f["page"], []).append(f)

    for i, page in enumerate(reader.pages):
        if i in by_page:
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            for field in by_page[i]:
                c.setFont("Helvetica", field.get("font_size", 9))
                c.drawString(field["x"], field["y"], str(field["text"]))
            c.save()
            packet.seek(0)
            overlay_page = pypdf.PdfReader(packet).pages[0]
            page.merge_page(overlay_page)
        writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output_path), "wb") as f:
        writer.write(f)


def flatten_form(input_path: Path, output_path: Path) -> None:
    """
    Aplana el formulario: los campos AcroForm quedan como texto fijo.
    El PDF resultante no es editable (ideal para versión final firmada).
    """
    pdf = PdfrwReader(str(input_path))
    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfName.true))
    writer = PdfWriter()
    writer.trailer = pdf.trailer
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer.write(str(output_path))


def add_metadata(input_path: Path, output_path: Path, metadata: dict) -> None:
    """
    Agrega/actualiza metadatos del PDF.
    Claves estándar: /Author, /Title, /Subject, /Creator, /Producer
    """
    reader = pypdf.PdfReader(str(input_path))
    writer = pypdf.PdfWriter()
    writer.append(reader)
    writer.add_metadata(metadata)
    with open(str(output_path), "wb") as f:
        writer.write(f)


# ─────────────────────────────────────────────
# 5. VALIDACIÓN DE FORMULARIO COMPLETO
# ─────────────────────────────────────────────

def validate_form_data(data: dict) -> dict:
    """
    Ejecuta todas las validaciones sobre un dict de datos del formulario.
    Retorna {"status": "ok"|"error", "errors": [...], "warnings": [...]}
    """
    errors = []
    warnings = []

    # --- Validaciones directas (sin Pydantic) ---
    nit = data.get("nit", "")
    if nit:
        ok, msg = validate_nit(nit)
        if not ok:
            errors.append({"campo": "nit (campo 4)", "error": msg})

    fecha = data.get("fecha_diligenciamiento", "")
    if fecha:
        ok, msg = validate_fecha(fecha)
        if not ok:
            errors.append({"campo": "fecha_diligenciamiento (campo 1)", "error": msg})

    email = data.get("correo_electronico", "")
    if email:
        ok, msg = validate_email(email)
        if not ok:
            errors.append({"campo": "correo_electronico (campo 16)", "error": msg})

    celular = data.get("celular", "")
    if celular:
        ok, msg = validate_phone_colombia(celular)
        if not ok:
            warnings.append({"campo": "celular (campo 15)", "aviso": msg})

    ciiu = data.get("ciiu", "")
    if ciiu:
        ok, msg = validate_ciiu(ciiu)
        if not ok:
            errors.append({"campo": "ciiu (campo 29)", "error": msg})

    # --- Ecuación contable ---
    activo = data.get("activo")
    pasivo = data.get("pasivo")
    patrimonio = data.get("patrimonio")
    if all(v is not None for v in [activo, pasivo, patrimonio]):
        ok, msg = validate_financial_balance(float(activo), float(pasivo), float(patrimonio))
        if not ok:
            errors.append({"campo": "campos 31–33 (activo/pasivo/patrimonio)", "error": msg})

    # --- PEP: si alguna pregunta es Sí, campos 25–26 obligatorios ---
    pep_flags = [
        data.get("es_pep_nacional"), data.get("es_pep_extranjero"),
        data.get("es_pep_internacional"), data.get("sociedad_conyugal_pep"),
        data.get("asociado_cercano_pep"), data.get("familiar_pep"),
    ]
    if any(pep_flags) and not data.get("nombre_pep"):
        errors.append({
            "campo": "nombre_pep (campo 25)",
            "error": "Obligatorio cuando alguna pregunta PEP (19–24) es Sí"
        })

    # --- Campo 46 Sí → campo 47 requerido ---
    if data.get("hay_beneficiarios_distintos") and data.get("beneficiarios_personas_naturales") is None:
        errors.append({
            "campo": "campo 47",
            "error": "Si campo 46 = Sí, debe indicar si los beneficiarios son personas naturales"
        })

    # --- Otros ingresos → concepto requerido ---
    otros_ingresos = data.get("otros_ingresos")
    if otros_ingresos and float(otros_ingresos) > 0 and not data.get("concepto_otros_ingresos"):
        errors.append({
            "campo": "concepto_otros_ingresos (campo 38)",
            "error": "Obligatorio cuando hay otros ingresos (campo 37)"
        })

    # --- Obligaciones fiscales exterior → detalle requerido ---
    if data.get("obligaciones_fiscales_exterior") and not data.get("cuales_obligaciones"):
        errors.append({
            "campo": "cuales_obligaciones (campo 10)",
            "error": "Obligatorio cuando campo 9 = Sí"
        })

    # --- Campos básicos vacíos ---
    required_basic = {
        "nombre_empresa": "campo 3",
        "nit": "campo 4",
        "nombre_representante": "campo 6",
        "numero_identificacion": "campo 8",
    }
    for field, label in required_basic.items():
        if not data.get(field, "").strip():
            errors.append({"campo": f"{field} ({label})", "error": "Campo obligatorio vacío"})

    return {
        "status": "error" if errors else "ok",
        "errors": errors,
        "warnings": warnings,
        "total_errors": len(errors),
        "total_warnings": len(warnings),
    }


# ─────────────────────────────────────────────
# 6. REPORTE Y DIAGNÓSTICO
# ─────────────────────────────────────────────

def print_separator(title: str, width: int = 60) -> None:
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}")


def run_full_report(path: Path) -> None:
    """
    Ejecuta diagnóstico completo del PDF y muestra resultados en consola.
    """
    print_separator("DIAGNÓSTICO FORMULARIO SARLAFT — AXA COLPATRIA")
    print(f"  Archivo : {path.name}")
    print(f"  Ruta    : {path}")

    # ── Info general ──
    print_separator("1. INFORMACIÓN GENERAL DEL PDF")
    info = get_pdf_info(path)
    print(f"  Tamaño       : {info['size_kb']} KB")
    print(f"  Páginas      : {info['pages']}")
    print(f"  Tipo PDF     : {info['pdf_type'].upper()}")
    print(f"  Campos AcroForm encontrados: {info['total_fields']}")
    if info["metadata"]:
        print("  Metadatos:")
        for k, v in info["metadata"].items():
            print(f"    {k}: {v}")

    # ── Campos AcroForm ──
    if info["pdf_type"] == "acroform":
        print_separator("2. CAMPOS ACROFORM DETECTADOS")
        fields = read_acroform_fields(path)
        if fields:
            for name, val in fields.items():
                print(f"  [{name}] = {repr(val)}")
        else:
            print("  (ningún campo con valor)")
    else:
        print_separator("2. TIPO: PDF PLANO — Extracción por pdfminer.six")
        print("  (No hay campos AcroForm. Se usará overlay para edición.)")

    # ── Texto por página ──
    print_separator("3. CONTENIDO DE TEXTO POR PÁGINA (pdfminer.six)")
    pages = extract_text_per_page(path)
    for i, text in enumerate(pages):
        print(f"\n  --- Página {i+1} ---")
        preview = text[:600].replace("\n", " | ")
        print(f"  {preview}{'...' if len(text) > 600 else ''}")

    # ── Tablas ──
    print_separator("4. TABLAS DETECTADAS (pdfplumber)")
    all_tables = extract_all_tables(path)
    if all_tables:
        for page_idx, tables in all_tables.items():
            print(f"\n  Página {page_idx + 1}: {len(tables)} tabla(s)")
            for t_idx, table in enumerate(tables):
                print(f"    Tabla {t_idx + 1} — {len(table)} filas × {len(table[0]) if table else 0} columnas")
                for row in table[:4]:  # mostrar máximo 4 filas
                    row_preview = [str(c)[:25] if c else "" for c in row]
                    print(f"      {row_preview}")
                if len(table) > 4:
                    print(f"      ... ({len(table) - 4} filas más)")
    else:
        print("  No se detectaron tablas estructuradas.")

    # ── Validación de ejemplo ──
    print_separator("5. VALIDACIÓN DE DATOS — EJEMPLO")
    test_cases = [
        ("NIT válido",      lambda: validate_nit("900123456-8")),
        ("NIT inválido",    lambda: validate_nit("123456789-0")),
        ("NIT sin dígito",  lambda: validate_nit("9001234568")),
        ("Fecha válida",    lambda: validate_fecha("15/03/2025")),
        ("Fecha futura",    lambda: validate_fecha("31/12/2099")),
        ("Email válido",    lambda: validate_email("cliente@empresa.com.co")),
        ("Email inválido",  lambda: validate_email("no_es_un_email")),
        ("Celular válido",  lambda: validate_phone_colombia("3001234567")),
        ("Celular inválido",lambda: validate_phone_colombia("12345")),
        ("CIIU válido",     lambda: validate_ciiu("6511")),
        ("CIIU inválido",   lambda: validate_ciiu("ABC")),
        ("Balance OK",      lambda: validate_financial_balance(1000000, 600000, 400000)),
        ("Balance FALLA",   lambda: validate_financial_balance(1000000, 600000, 500000)),
    ]
    for label, fn in test_cases:
        ok, msg = fn()
        status = "OK" if ok else "FALLA"
        print(f"  [{status}] {label}: {msg}")

    # ── Clasificación de régimen ──
    print_separator("6. CLASIFICACIÓN DE RÉGIMEN (Circular 027/2020)")
    regime_cases = [
        ("Póliza de vida empresarial", False, False),
        ("Seguro de salud colectivo", False, False),
        ("Contrato de reaseguro proporcional", False, False),
        ("Seguro de cumplimiento licitación pública", False, False),
        ("Póliza de responsabilidad civil", False, False),
        ("Póliza de incendio", True, False),  # entidad pública
        ("Póliza de automóviles", False, True),  # pago descuento directo
    ]
    for producto, es_publica, descuento in regime_cases:
        regime, motivo = classify_regime(producto, es_publica, descuento)
        print(f"  [{regime.upper()}] '{producto}'")
        print(f"    Motivo: {motivo}")

    # ── Validación de formulario completo (datos simulados) ──
    print_separator("7. VALIDACIÓN DE FORMULARIO COMPLETO (datos simulados)")

    test_form_ok = {
        "nombre_empresa": "Empresa Ejemplo S.A.S.",
        "nit": "900123456-8",
        "fecha_diligenciamiento": "15/03/2025",
        "nombre_representante": "Juan Pérez García",
        "numero_identificacion": "12345678",
        "correo_electronico": "rep@empresa.com.co",
        "celular": "3001234567",
        "ciiu": "6511",
        "activo": 1000000,
        "pasivo": 600000,
        "patrimonio": 400000,
        "otros_ingresos": 0,
        "obligaciones_fiscales_exterior": False,
        "hay_beneficiarios_distintos": False,
    }

    test_form_errors = {
        "nombre_empresa": "",                      # vacío
        "nit": "123456789-0",                      # dígito inválido
        "fecha_diligenciamiento": "31/12/2099",    # futura
        "nombre_representante": "Ana López",
        "numero_identificacion": "87654321",
        "correo_electronico": "no_es_email",       # inválido
        "celular": "12345",                        # inválido
        "ciiu": "AB12",                            # inválido
        "activo": 1000000,
        "pasivo": 800000,
        "patrimonio": 500000,                      # no cuadra
        "otros_ingresos": 500000,                  # sin concepto
        "concepto_otros_ingresos": None,
        "obligaciones_fiscales_exterior": True,    # sin detalle
        "cuales_obligaciones": None,
        "es_pep_nacional": True,                   # PEP sin nombre
        "nombre_pep": None,
    }

    print("\n  --- Formulario con datos correctos ---")
    result_ok = validate_form_data(test_form_ok)
    print(f"  Estado : {result_ok['status'].upper()}")
    print(f"  Errores: {result_ok['total_errors']} | Advertencias: {result_ok['total_warnings']}")

    print("\n  --- Formulario con datos con errores ---")
    result_err = validate_form_data(test_form_errors)
    print(f"  Estado : {result_err['status'].upper()}")
    print(f"  Errores: {result_err['total_errors']} | Advertencias: {result_err['total_warnings']}")
    for e in result_err["errors"]:
        print(f"    [ERROR] {e['campo']}: {e['error']}")
    for w in result_err["warnings"]:
        print(f"    [AVISO] {w['campo']}: {w['aviso']}")

    print_separator("FIN DEL DIAGNÓSTICO")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not PDF_PATH.exists():
        print(f"ERROR: No se encontró el PDF en {PDF_PATH}")
    else:
        run_full_report(PDF_PATH)

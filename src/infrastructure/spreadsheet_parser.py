"""Utilitário para leitura, parsing e sanitização de planilhas de equipamentos (.xlsx / .csv)."""

import csv
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import openpyxl


@dataclass
class ParsedSpreadsheetRow:
    """Representação estruturada de uma linha de equipamento parseada."""

    row_number: int
    equipment_type: str
    location: str
    status: str
    description: str
    patrimony_number: str | None = None
    serial_number: str | None = None
    brand: str | None = None
    hostname: str | None = None
    model: str | None = None
    product_number: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    printer_identifier: str | None = None
    windows_key: str | None = None
    last_maintenance_at: datetime | None = None
    hist_mov: str | None = None
    notes: str | None = None


@dataclass
class ParsedSpreadsheet:
    """Resultado do parsing completo da planilha."""

    filename: str
    detected_sheet: str | None
    headers: list[str]
    rows: list[ParsedSpreadsheetRow]


def _normalize_header(header: str | None) -> str:
    """Normaliza um cabeçalho removendo acentuação, caracteres especiais e espaços extras."""
    if not header:
        return ""
    text = str(header).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def _map_headers(raw_headers: list[Any]) -> dict[str, int]:
    """Mapeia os cabeçalhos encontrados para os campos canônicos do sistema."""
    mapping: dict[str, int] = {}

    canonical_patterns: dict[str, list[str]] = {
        "equipment_type": ["tipo", "tipodeequipamento", "categoria"],
        "location": ["localizacao", "local", "setor", "unidade"],
        "status": ["situacao", "status", "estado"],
        "description": ["descricao", "especificacao", "equipamento"],
        "patrimony_number": [
            "npatrimonio",
            "nopatrimonio",
            "numeropatrimonio",
            "patrimonio",
            "tombo",
            "ntombo",
            "notombo",
        ],
        "serial_number": [
            "nserie",
            "noserie",
            "numeroserie",
            "serie",
            "serial",
            "serialnumber",
            "ns",
        ],
        "brand": ["marca", "fabricante"],
        "model": [
            "modelo",
            "model",
            "nproduto",
            "noproduto",
            "numeroproduto",
            "pn",
            "partnumber",
            "produto",
        ],
        "ip_address": ["ip", "ipaddress", "enderecoip", "ipv4"],
        "mac_address": ["mac", "macaddress", "enderecomac"],
        "printer_identifier": ["identificadorimpressora", "idimpressora", "impressoraid"],
        "last_maintenance_at": [
            "ultimamanutencao",
            "datamanutencao",
            "manutencao",
            "ultimaintervencao",
        ],
        "windows_key": ["chavewindows", "licencawindows", "chave", "licenca", "windowskey"],
        "hist_mov": [
            "historicodemovimentacoes",
            "historicodemovimentacao",
            "historicomovimentacoes",
            "historico",
            "movimentacoes",
            "intervencoes",
        ],
        "hostname": ["hostname", "host", "nomered"],
        "notes": ["observacoes", "observacao", "obs", "comentarios", "notas"],
    }

    for idx, raw_h in enumerate(raw_headers):
        if raw_h is None:
            continue
        norm_h = _normalize_header(str(raw_h))
        if not norm_h:
            continue
        for field, patterns in canonical_patterns.items():
            if field not in mapping and any(p in norm_h or norm_h in p for p in patterns):
                mapping[field] = idx
                break

    return mapping


def _clean_str(value: Any) -> str | None:
    """Limpa e formata um valor string, retornando None se vazio."""
    if value is None:
        return None
    val_str = str(value).strip()
    return val_str if val_str else None


def _parse_datetime(value: Any) -> datetime | None:
    """Converte um valor de data/hora para datetime com timezone UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    val_str = str(value).strip()
    if not val_str:
        return None

    date_formats = [
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def parse_spreadsheet(file_bytes: bytes, filename: str) -> ParsedSpreadsheet:
    """
    Lê o conteúdo de um arquivo (.xlsx, .xls ou .csv) e retorna as linhas estruturadas.
    Lança ValueError caso o arquivo seja inválido ou não contenha dados.
    """
    if not file_bytes:
        raise ValueError("O arquivo enviado está vazio.")

    lower_filename = filename.lower()

    if lower_filename.endswith((".xlsx", ".xlsm", ".xltx", ".xltm", ".xls")):
        return _parse_excel(file_bytes, filename)
    elif lower_filename.endswith(".csv"):
        return _parse_csv(file_bytes, filename)
    else:
        raise ValueError(
            f"Formato de arquivo não suportado para '{filename}'. Use arquivos .xlsx ou .csv."
        )


def _parse_excel(file_bytes: bytes, filename: str) -> ParsedSpreadsheet:
    """Faz o parsing de um arquivo Excel via openpyxl."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o arquivo Excel: {str(exc)}") from exc

    if not wb.sheetnames:
        raise ValueError("A planilha Excel não contém abas.")

    target_sheet_name = wb.sheetnames[0]
    for s_name in wb.sheetnames:
        norm_s = _normalize_header(s_name)
        if "patrimonio" in norm_s or "ativo" in norm_s or "equipamento" in norm_s:
            target_sheet_name = s_name
            break

    sheet = wb[target_sheet_name]
    rows_iter = sheet.iter_rows(values_only=True)

    try:
        first_row = next(rows_iter)
    except StopIteration:
        raise ValueError(f"A aba '{target_sheet_name}' está vazia.")

    raw_headers = list(first_row)
    header_mapping = _map_headers(raw_headers)

    headers_display = [str(h).strip() for h in raw_headers if h is not None and str(h).strip()]
    parsed_rows: list[ParsedSpreadsheetRow] = []

    for row_idx, row_values in enumerate(rows_iter, start=2):
        if not any(v is not None and str(v).strip() for v in row_values):
            continue

        def get_val(field: str) -> Any:
            idx = header_mapping.get(field)
            if idx is not None and idx < len(row_values):
                return row_values[idx]
            return None

        eq_type = _clean_str(get_val("equipment_type")) or "OUTROS"
        loc = _clean_str(get_val("location")) or "GERAL"
        status = _clean_str(get_val("status")) or "Em uso"
        desc = _clean_str(get_val("description")) or eq_type
        pat = _clean_str(get_val("patrimony_number"))
        ser = _clean_str(get_val("serial_number"))
        brand = _clean_str(get_val("brand"))
        host = _clean_str(get_val("hostname"))
        model = _clean_str(get_val("model"))
        ip_addr = _clean_str(get_val("ip_address"))
        mac_addr = _clean_str(get_val("mac_address"))
        printer_id = _clean_str(get_val("printer_identifier"))
        win_key = _clean_str(get_val("windows_key"))
        last_maint = _parse_datetime(get_val("last_maintenance_at"))
        hist_mov = _clean_str(get_val("hist_mov"))
        notes = _clean_str(get_val("notes"))

        parsed_rows.append(
            ParsedSpreadsheetRow(
                row_number=row_idx,
                equipment_type=eq_type,
                location=loc,
                status=status,
                description=desc,
                patrimony_number=pat,
                serial_number=ser,
                brand=brand,
                hostname=host,
                model=model,
                product_number=model,
                ip_address=ip_addr,
                mac_address=mac_addr,
                printer_identifier=printer_id,
                windows_key=win_key,
                last_maintenance_at=last_maint,
                hist_mov=hist_mov,
                notes=notes,
            )
        )

    return ParsedSpreadsheet(
        filename=filename,
        detected_sheet=target_sheet_name,
        headers=headers_display,
        rows=parsed_rows,
    )


def _parse_csv(file_bytes: bytes, filename: str) -> ParsedSpreadsheet:
    """Faz o parsing de um arquivo CSV com detecção de encoding e delimitador."""
    content_str: str | None = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            content_str = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if content_str is None:
        raise ValueError("Não foi possível decodificar o arquivo CSV com codificações suportadas.")

    lines = [line for line in content_str.splitlines() if line.strip()]
    if not lines:
        raise ValueError("O arquivo CSV está vazio.")

    sample = "\n".join(lines[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ";" if ";" in lines[0] else ","

    reader = csv.reader(lines, delimiter=delimiter)
    raw_headers = next(reader)

    header_mapping = _map_headers(raw_headers)
    headers_display = [str(h).strip() for h in raw_headers if str(h).strip()]
    parsed_rows: list[ParsedSpreadsheetRow] = []

    for row_idx, row_values in enumerate(reader, start=2):
        if not any(v.strip() for v in row_values):
            continue

        def get_val(field: str) -> Any:
            idx = header_mapping.get(field)
            if idx is not None and idx < len(row_values):
                return row_values[idx]
            return None

        eq_type = _clean_str(get_val("equipment_type")) or "OUTROS"
        loc = _clean_str(get_val("location")) or "GERAL"
        status = _clean_str(get_val("status")) or "Em uso"
        desc = _clean_str(get_val("description")) or eq_type
        pat = _clean_str(get_val("patrimony_number"))
        ser = _clean_str(get_val("serial_number"))
        brand = _clean_str(get_val("brand"))
        host = _clean_str(get_val("hostname"))
        model = _clean_str(get_val("model"))
        ip_addr = _clean_str(get_val("ip_address"))
        mac_addr = _clean_str(get_val("mac_address"))
        printer_id = _clean_str(get_val("printer_identifier"))
        win_key = _clean_str(get_val("windows_key"))
        last_maint = _parse_datetime(get_val("last_maintenance_at"))
        hist_mov = _clean_str(get_val("hist_mov"))
        notes = _clean_str(get_val("notes"))

        parsed_rows.append(
            ParsedSpreadsheetRow(
                row_number=row_idx,
                equipment_type=eq_type,
                location=loc,
                status=status,
                description=desc,
                patrimony_number=pat,
                serial_number=ser,
                brand=brand,
                hostname=host,
                model=model,
                product_number=model,
                ip_address=ip_addr,
                mac_address=mac_addr,
                printer_identifier=printer_id,
                windows_key=win_key,
                last_maintenance_at=last_maint,
                hist_mov=hist_mov,
                notes=notes,
            )
        )

    return ParsedSpreadsheet(
        filename=filename,
        detected_sheet=None,
        headers=headers_display,
        rows=parsed_rows,
    )

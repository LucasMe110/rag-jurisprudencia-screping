import calendar
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://eproc1g.tjsc.jus.br"
LISTAR_RESULTADOS = f"{BASE}/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
PAGINAR = f"{BASE}/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE,
    "Referer": LISTAR_RESULTADOS,
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

PAGE_SIZE = 100  # 100 registros por página reduz requests 10x (US→Brasil ~14s/req)


def extract_field(card, label_pt: str) -> str:
    for row in card.select("div.row"):
        lab = row.select_one(".resLabel")
        val = row.select_one(".resValue")
        if not lab or not val:
            continue
        if lab.get_text(" ", strip=True).upper() == label_pt.upper():
            return val.get_text(" ", strip=True)
    return ""


def extract_processo(card) -> str:
    a = card.select_one("a.numero-processo")
    if a:
        return a.get_text(" ", strip=True)
    processo_val = extract_field(card, "PROCESSO")
    if processo_val:
        return processo_val.split()[0].strip()
    return ""


def parse_results_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for card in soup.select("div.resultadoItem"):
        processo = extract_processo(card)
        orgao = extract_field(card, "ÓRGÃO JULGADOR")
        data_julg = extract_field(card, "DATA DO JULGAMENTO")
        data_pub = extract_field(card, "DATA DA PUBLICAÇÃO")
        relator = extract_field(card, "RELATOR")
        decisao = extract_field(card, "DECISÃO")
        if not decisao:
            decisao = extract_field(card, "EMENTA")

        items.append({
            "processo": processo,
            "orgao_julgador": orgao,
            "data_julgamento": data_julg,
            "data_publicacao": data_pub,
            "relator": relator,
            "decisao": decisao,
        })

    return items


def scrape_month(
    year: int,
    month: int,
    sleep: float = 1.0,
    failed_pages: list | None = None,
) -> list[dict]:
    _, last_day = calendar.monthrange(year, month)
    date_start = f"01/{month:02d}/{year}"
    date_end = f"{last_day:02d}/{month:02d}/{year}"
    month_str = f"{year}-{month:02d}"

    session = requests.Session()
    records: list[dict] = []
    consecutive_no_results = 0
    page = 1

    while consecutive_no_results < 3:
        html = None
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                html = fetch_page(session, page, date_start, date_end)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)

        if last_error is not None:
            if failed_pages is not None:
                failed_pages.append(
                    {"month": month_str, "page": page, "error": str(last_error)}
                )
            consecutive_no_results += 1
            page += 1
            continue

        items = parse_results_page(html)
        if items:
            consecutive_no_results = 0
            records.extend(items)
        else:
            consecutive_no_results += 1

        page += 1
        if sleep > 0:
            time.sleep(sleep)

    return records


def fetch_page(session: requests.Session, page: int, date_start: str = "", date_end: str = "") -> str:
    payload = {
        "acao": "jurisprudencia@jurisprudencia/ajax_paginar_resultado",
        "txtPesquisa": "",
        "hdnExibirPesquisaAvancada": "",
        "hdnUrlCarregarListasCombobox": "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_carregar_listas_pesquisa",
        "rdoCampo": "I",
        "txtProcesso": "",
        "dtDecisaoInicio": date_start,
        "dtDecisaoFim": date_end,
        "hdnDecisaoInicio": "",
        "hdnDecisaoFim": "",
        "dtPublicacaoInicio": "",
        "dtPublicacaoFim": "",
        "hdnPublicacaoInicio": "",
        "hdnPublicacaoFim": "",
        "selOrdenacao": "1",
        "hdnUrlPaginar": "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado",
        "selTamanhoPagina": str(PAGE_SIZE),
        "hdnTotalPaginas": "999999",
        "hdnPaginaAtual": str(page),
        "hdnTotalResultado": "",
        "hdnDocsSelecionados": "",
    }

    resp = session.post(PAGINAR, data=payload, headers=HEADERS, timeout=45)
    resp.encoding = "ISO-8859-1"
    return resp.text

import calendar
import time
import requests
from bs4 import BeautifulSoup

# Registro de tribunais — todos rodam a MESMA implementação eproc
# (rota acao=jurisprudencia@jurisprudencia). Só muda o host base.
TRIBUNAIS = {
    "tjsc": {"base": "https://eproc1g.tjsc.jus.br"},
    "tjsp": {"base": "https://eproc1g.tjsp.jus.br"},
    "tjrj": {"base": "https://eproc1g.tjrj.jus.br"},
}

PAGE_SIZE = 100  # 100 registros por página reduz requests 10x (US→Brasil ~14s/req)


def _urls(tribunal: str) -> tuple[str, str]:
    """Deriva (LISTAR_RESULTADOS, PAGINAR) a partir do base do tribunal.

    Levanta ValueError se o tribunal não estiver registrado em TRIBUNAIS.
    """
    if tribunal not in TRIBUNAIS:
        raise ValueError(
            f"Tribunal inválido: {tribunal!r}. Disponíveis: {sorted(TRIBUNAIS)}"
        )
    base = TRIBUNAIS[tribunal]["base"]
    listar = f"{base}/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
    paginar = f"{base}/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado"
    return listar, paginar


def _headers(tribunal: str) -> dict:
    """Headers da requisição com Origin/Referer derivados do base do tribunal."""
    listar, _ = _urls(tribunal)
    base = TRIBUNAIS[tribunal]["base"]
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base,
        "Referer": listar,
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }


def extract_field(card, *labels: str) -> str:
    """Retorna o valor do primeiro .resLabel cujo texto casa com algum dos labels.

    Itera .resLabel direto (não div.row): no TJSC os campos ficam em div.row,
    mas no TJSP/TJRJ vários ficam em <div class="col-12 col-md-4">. Para cada
    label encontrado, o .resValue par é o irmão seguinte; se não houver, busca
    dentro do parent.
    """
    wanted = {lab.upper() for lab in labels}
    for lab in card.select(".resLabel"):
        if lab.get_text(" ", strip=True).upper() not in wanted:
            continue
        val = lab.find_next_sibling(class_="resValue")
        if val is None and lab.parent is not None:
            val = lab.parent.select_one(".resValue")
        if val is not None:
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
        relator = extract_field(card, "RELATOR", "RELATORA", "MAGISTRADA", "MAGISTRADO")
        decisao = extract_field(card, "DECISÃO") or extract_field(card, "EMENTA")

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
    tribunal: str = "tjsc",
) -> list[dict]:
    _urls(tribunal)  # valida o tribunal cedo (levanta ValueError se inválido)
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
                html = fetch_page(session, page, date_start, date_end, tribunal=tribunal)
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
            for item in items:
                item["tribunal"] = tribunal
            records.extend(items)
        else:
            consecutive_no_results += 1

        page += 1
        if sleep > 0:
            time.sleep(sleep)

    return records


def fetch_page(
    session: requests.Session,
    page: int,
    date_start: str = "",
    date_end: str = "",
    tribunal: str = "tjsc",
) -> str:
    _, paginar = _urls(tribunal)
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

    resp = session.post(paginar, data=payload, headers=_headers(tribunal), timeout=45)
    resp.encoding = "ISO-8859-1"
    return resp.text

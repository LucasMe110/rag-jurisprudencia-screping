import time
import json
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

# ─── Configurações ────────────────────────────────────────────────────────────
PAGINA_INICIO = 1
PAGINA_FIM    = 150112      # Altere para quantas páginas quiser raspar
PAGE_SIZE     = 10     # 10 ou 100 (conforme o site permite)
SLEEP_ENTRE_PAGINAS = 1  # segundos entre requisições
OUTPUT_FILE   = "processos.json"
# ──────────────────────────────────────────────────────────────────────────────


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


def parse_results_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for card in soup.select("div.resultadoItem"):
        processo  = extract_processo(card)
        orgao     = extract_field(card, "ÓRGÃO JULGADOR")
        data_julg = extract_field(card, "DATA DO JULGAMENTO")
        data_pub  = extract_field(card, "DATA DA PUBLICAÇÃO")
        relator   = extract_field(card, "RELATOR")
        decisao   = extract_field(card, "DECISÃO")
        if not decisao:
            decisao = extract_field(card, "EMENTA")

        items.append({
            "processo":        processo,
            "orgao_julgador":  orgao,
            "data_julgamento": data_julg,
            "data_publicacao": data_pub,
            "relator":         relator,
            "decisao":         decisao,
        })

    return items


def fetch_page(session: requests.Session, page: int) -> str:
    payload = {
        "acao": "jurisprudencia@jurisprudencia/ajax_paginar_resultado",
        "txtPesquisa": "",
        "hdnExibirPesquisaAvancada": "",
        "hdnUrlCarregarListasCombobox": "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_carregar_listas_pesquisa",
        "rdoCampo": "I",
        "txtProcesso": "",
        "dtDecisaoInicio": "",
        "dtDecisaoFim": "",
        "hdnDecisaoInicio": "",
        "hdnDecisaoFim": "",
        "dtPublicacaoInicio": "",
        "dtPublicacaoFim": "",
        "hdnPublicacaoInicio": "",
        "hdnPublicacaoFim": "",
        "selOrdenacao": "1",
        "hdnUrlPaginar": "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado",
        "selTamanhoPagina": str(PAGE_SIZE),
        "hdnTotalPaginas": "383276",
        "hdnPaginaAtual": str(page),
        "hdnTotalResultado": "3832760",
        "hdnDocsSelecionados": ""
    }

    resp = session.post(PAGINAR, data=payload, headers=HEADERS, timeout=30)
    resp.encoding = "ISO-8859-1"
    return resp.text


def main():
    session = requests.Session()

    print("Iniciando sessão...")
    r = session.get(LISTAR_RESULTADOS, headers=HEADERS, timeout=30)
    print(f"Status inicial: {r.status_code}")

    todos = []

    for page in range(PAGINA_INICIO, PAGINA_FIM + 1):
        print(f"Buscando página {page}...", end=" ")
        html = fetch_page(session, page)
        items = parse_results_page(html)
        print(f"{len(items)} itens")

        if not items:
            print("Nenhum item encontrado, encerrando.")
            break

        todos.extend(items)
        time.sleep(SLEEP_ENTRE_PAGINAS)

    resultado = {
        "total_casos": len(todos),
        "casos": todos
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nConcluído! {len(todos)} casos salvos em '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
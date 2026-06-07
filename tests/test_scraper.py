from screping.scraper import parse_results_page, extract_processo
from bs4 import BeautifulSoup

TWO_CARDS_HTML = """
<html><body>
<div class="card mb-3 resultadoItem" id="resultado1">
    <div class="card-body">
        <div class="row">
            <div class="col">
                <a class="numero-processo">0001234-56.2018.8.24.0001</a>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">ÓRGÃO JULGADOR</div>
                <div class="resValue">Câmara Especial</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">DATA DO JULGAMENTO</div>
                <div class="resValue">01/01/2018</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">DATA DA PUBLICAÇÃO</div>
                <div class="resValue">15/01/2018</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">RELATOR</div>
                <div class="resValue">Dr. João Silva</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">DECISÃO</div>
                <div class="resValue">Recurso provido.</div>
            </div>
        </div>
    </div>
</div>
<div class="card mb-3 resultadoItem" id="resultado2">
    <div class="card-body">
        <div class="row">
            <div class="col">
                <div class="resLabel">PROCESSO</div>
                <div class="resValue">0009876-54.2018.8.24.0002</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">ÓRGÃO JULGADOR</div>
                <div class="resValue">Segunda Câmara de Direito Civil</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">DATA DO JULGAMENTO</div>
                <div class="resValue">05/03/2018</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">DATA DA PUBLICAÇÃO</div>
                <div class="resValue">20/03/2018</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">RELATOR</div>
                <div class="resValue">Dra. Maria Santos</div>
            </div>
        </div>
        <div class="row">
            <div class="col">
                <div class="resLabel">EMENTA</div>
                <div class="resValue">Apelação desprovida.</div>
            </div>
        </div>
    </div>
</div>
</body></html>
"""

EMPTY_HTML = "<html><body><div id='bodyResultados'></div></body></html>"

CARD_WITH_LINK_HTML = """
<div class="resultadoItem">
    <a class="numero-processo">0001234-56.2018.8.24.0001</a>
    <div class="row">
        <div class="resLabel">PROCESSO</div>
        <div class="resValue">FALLBACK_NUMBER</div>
    </div>
</div>
"""

CARD_WITHOUT_LINK_HTML = """
<div class="resultadoItem">
    <div class="row">
        <div class="resLabel">PROCESSO</div>
        <div class="resValue">0009876-54.2018.8.24.0002 extra text here</div>
    </div>
</div>
"""


def test_parse_results_page_two_cards():
    items = parse_results_page(TWO_CARDS_HTML)
    assert len(items) == 2

    first = items[0]
    assert first["processo"] == "0001234-56.2018.8.24.0001"
    assert first["orgao_julgador"] == "Câmara Especial"
    assert first["data_julgamento"] == "01/01/2018"
    assert first["data_publicacao"] == "15/01/2018"
    assert first["relator"] == "Dr. João Silva"
    assert first["decisao"] == "Recurso provido."

    second = items[1]
    assert second["processo"] == "0009876-54.2018.8.24.0002"
    assert second["orgao_julgador"] == "Segunda Câmara de Direito Civil"
    assert second["data_julgamento"] == "05/03/2018"
    assert second["data_publicacao"] == "20/03/2018"
    assert second["relator"] == "Dra. Maria Santos"
    assert second["decisao"] == "Apelação desprovida."


def test_parse_results_page_empty_html():
    items = parse_results_page(EMPTY_HTML)
    assert items == []


def test_extract_processo_with_link():
    soup = BeautifulSoup(CARD_WITH_LINK_HTML, "html.parser")
    card = soup.select_one("div.resultadoItem")
    result = extract_processo(card)
    assert result == "0001234-56.2018.8.24.0001"


def test_extract_processo_fallback_to_field():
    soup = BeautifulSoup(CARD_WITHOUT_LINK_HTML, "html.parser")
    card = soup.select_one("div.resultadoItem")
    result = extract_processo(card)
    assert result == "0009876-54.2018.8.24.0002"


def test_parse_results_page_ementa_fallback():
    """EMENTA is used as decisao when DECISÃO field is absent."""
    items = parse_results_page(TWO_CARDS_HTML)
    second = items[1]
    assert second["decisao"] == "Apelação desprovida."

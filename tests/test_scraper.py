import requests
from unittest.mock import patch, call
from screping.scraper import parse_results_page, extract_processo, scrape_month
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


SINGLE_CARD_HTML = """
<html><body>
<div class="resultadoItem">
    <a class="numero-processo">0001234-56.2018.8.24.0001</a>
    <div class="row"><div class="resLabel">DATA DO JULGAMENTO</div><div class="resValue">15/01/2018</div></div>
    <div class="row"><div class="resLabel">DECISÃO</div><div class="resValue">Provido.</div></div>
</div>
</body></html>
"""


def test_parse_results_page_ementa_fallback():
    """EMENTA is used as decisao when DECISÃO field is absent."""
    items = parse_results_page(TWO_CARDS_HTML)
    second = items[1]
    assert second["decisao"] == "Apelação desprovida."


EMPTY = "<html><body></body></html>"


def test_scrape_month_calls_fetch_with_correct_dates():
    with patch("screping.scraper.fetch_page", return_value=EMPTY) as mock_fetch, \
         patch("time.sleep"):
        scrape_month(2018, 1, sleep=0)
    first_args = mock_fetch.call_args_list[0][0]
    assert first_args[2] == "01/01/2018"
    assert first_args[3] == "31/01/2018"


def test_scrape_month_february_last_day():
    with patch("screping.scraper.fetch_page", return_value=EMPTY) as mock_fetch, \
         patch("time.sleep"):
        scrape_month(2020, 2, sleep=0)  # leap year
    first_args = mock_fetch.call_args_list[0][0]
    assert first_args[3] == "29/02/2020"


def test_scrape_month_stops_after_3_consecutive_empty():
    with patch("screping.scraper.fetch_page", return_value=EMPTY) as mock_fetch, \
         patch("time.sleep"):
        records = scrape_month(2018, 1, sleep=0)
    assert records == []
    assert mock_fetch.call_count == 3


def test_scrape_month_resets_consecutive_count_on_results():
    responses = {2: SINGLE_CARD_HTML}

    def side_effect(session, page, date_start, date_end):
        return responses.get(page, EMPTY)

    with patch("screping.scraper.fetch_page", side_effect=side_effect), \
         patch("time.sleep"):
        records = scrape_month(2018, 1, sleep=0)

    # page 1: empty(1), page 2: 1 result (reset), pages 3/4/5: empty(1/2/3) → stop
    assert len(records) == 1
    assert records[0]["processo"] == "0001234-56.2018.8.24.0001"


def test_scrape_month_retries_on_exception():
    call_counter = [0]

    def side_effect(session, page, date_start, date_end):
        call_counter[0] += 1
        if call_counter[0] <= 2:
            raise requests.exceptions.Timeout("timeout")
        return EMPTY

    with patch("screping.scraper.fetch_page", side_effect=side_effect), \
         patch("time.sleep"):
        records = scrape_month(2018, 1, sleep=0)

    # 2 failures + 1 success on page 1, then 2 more empty pages = 3 total calls + 2 extra
    assert call_counter[0] >= 3
    assert records == []


def test_scrape_month_records_failed_pages():
    failed = []

    def always_fail(session, page, date_start, date_end):
        raise requests.exceptions.ConnectionError("connection refused")

    with patch("screping.scraper.fetch_page", side_effect=always_fail), \
         patch("time.sleep"):
        records = scrape_month(2018, 1, sleep=0, failed_pages=failed)

    assert records == []
    assert len(failed) == 3
    assert failed[0]["month"] == "2018-01"
    assert failed[0]["page"] == 1
    assert "connection refused" in failed[0]["error"]


def test_scrape_month_retry_sleep_called():
    call_counter = [0]

    def side_effect(session, page, date_start, date_end):
        call_counter[0] += 1
        if call_counter[0] == 1:
            raise requests.exceptions.Timeout("timeout")
        return EMPTY

    sleep_calls = []
    with patch("screping.scraper.fetch_page", side_effect=side_effect), \
         patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        scrape_month(2018, 1, sleep=0)

    # Should have slept 2^0=1 before the first retry
    assert 1 in sleep_calls

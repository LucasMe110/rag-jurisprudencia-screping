from unittest.mock import patch, MagicMock
import numpy as np
from screping.embedder import generate_embeddings


def test_generate_embeddings_adds_embedding_field():
    records = [
        {"processo": "001", "decisao": "Recurso provido."},
        {"processo": "002", "decisao": ""},
    ]
    mock_vectors = np.array([[0.1] * 768, [0.2] * 768])

    with patch("screping.embedder.SentenceTransformer") as MockModel:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = mock_vectors
        MockModel.return_value = mock_instance

        result = generate_embeddings(records)

    assert "embedding" in result[0]
    assert len(result[0]["embedding"]) == 768
    assert "embedding" in result[1]


def test_generate_embeddings_applies_passage_prefix():
    records = [{"processo": "001", "decisao": "Texto da decisão."}]
    mock_vectors = np.array([[0.1] * 768])

    with patch("screping.embedder.SentenceTransformer") as MockModel:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = mock_vectors
        MockModel.return_value = mock_instance

        generate_embeddings(records)

        texts = mock_instance.encode.call_args[0][0]
        assert texts[0] == "passage: Texto da decisão."


def test_generate_embeddings_handles_none_decisao():
    records = [{"processo": "001", "decisao": None}]
    mock_vectors = np.array([[0.0] * 768])

    with patch("screping.embedder.SentenceTransformer") as MockModel:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = mock_vectors
        MockModel.return_value = mock_instance

        generate_embeddings(records)

        texts = mock_instance.encode.call_args[0][0]
        assert texts[0] == "passage: "


def test_generate_embeddings_uses_correct_encode_params():
    records = [{"processo": "001", "decisao": "Texto."}]
    mock_vectors = np.array([[0.1] * 768])

    with patch("screping.embedder.SentenceTransformer") as MockModel:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = mock_vectors
        MockModel.return_value = mock_instance

        generate_embeddings(records)

        kwargs = mock_instance.encode.call_args[1]
        assert kwargs.get("batch_size") == 256
        assert kwargs.get("normalize_embeddings") is True

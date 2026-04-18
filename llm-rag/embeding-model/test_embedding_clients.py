import asyncio

from client import OllamaEmbeddingClient, RemoteEmbeddingClient
from providers import PROVIDERS


def test_openai_dimensions_payload() -> None:
    client = object.__new__(RemoteEmbeddingClient)
    client.provider = PROVIDERS["openai"]
    client.model = "text-embedding-3-small"
    client.dimensions = 512

    payload = client._build_payload(["hello"], is_query=False)

    assert payload == {
        "model": "text-embedding-3-small",
        "input": "hello",
        "encoding_format": "float",
        "dimensions": 512,
    }


def test_voyage_query_payload() -> None:
    client = object.__new__(RemoteEmbeddingClient)
    client.provider = PROVIDERS["voyage"]
    client.model = "voyage-4-lite"
    client.dimensions = 256

    payload = client._build_payload(["what is rag"], is_query=True)

    assert payload["input_type"] == "query"
    assert payload["output_dimension"] == 256
    assert payload["output_dtype"] == "float"


def test_jina_document_payload() -> None:
    client = object.__new__(RemoteEmbeddingClient)
    client.provider = PROVIDERS["jina"]
    client.model = "jina-embeddings-v3"
    client.dimensions = None

    payload = client._build_payload(["doc-1", "doc-2"], is_query=False)

    assert payload == {
        "model": "jina-embeddings-v3",
        "input": ["doc-1", "doc-2"],
        "normalized": True,
        "embedding_type": "float",
        "task": "retrieval.passage",
    }


def test_ollama_payload() -> None:
    client = object.__new__(OllamaEmbeddingClient)
    client.provider = PROVIDERS["ollama"]
    client.model = "bge-m3"
    client.dimensions = 768

    payload = client._build_payload(["hello", "world"], is_query=False)

    assert payload == {
        "model": "bge-m3",
        "input": ["hello", "world"],
        "dimensions": 768,
    }


def test_ollama_response_parse() -> None:
    client = object.__new__(OllamaEmbeddingClient)
    client.provider = PROVIDERS["ollama"]
    client.model = "bge-m3"

    response = client._parse_response(
        {
            "model": "bge-m3",
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "total_duration": 100,
            "load_duration": 20,
            "prompt_eval_count": 2,
        }
    )

    assert response.model == "bge-m3"
    assert response.vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert response.usage == {
        "total_duration": 100,
        "load_duration": 20,
        "prompt_eval_count": 2,
    }


def test_batch_encode_collects_order() -> None:
    client = object.__new__(RemoteEmbeddingClient)
    client.provider = PROVIDERS["openai"]
    client.model = "text-embedding-3-small"

    def fake_embed(texts: list[str], is_query: bool):
        return type(
            "FakeResponse",
            (),
            {"vectors": [[float(index), float(len(text))] for index, text in enumerate(texts)]},
        )()

    client._embed = fake_embed  # type: ignore[method-assign]

    vectors = asyncio.run(
        client.batch_encode(
            ["aa", "bbb", "cccc", "ddddd", "eeeeee"],
            batch_size=2,
            max_concurrency=2,
        )
    )

    assert vectors == [
        [0.0, 2.0],
        [1.0, 3.0],
        [0.0, 4.0],
        [1.0, 5.0],
        [0.0, 6.0],
    ]

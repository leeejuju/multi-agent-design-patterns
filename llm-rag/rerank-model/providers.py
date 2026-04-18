from dataclasses import dataclass, field


@dataclass(frozen=True)
class RerankProvider:
    name: str
    endpoint: str
    api_key_env: str
    default_model: str
    recommended_models: tuple[str, ...]
    top_n_param: str | None = None
    extra_body: dict[str, object] = field(default_factory=dict)


PROVIDERS: dict[str, RerankProvider] = {
    "dashscope": RerankProvider(
        name="dashscope",
        endpoint="https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="qwen3-rerank",
        recommended_models=("qwen3-rerank", "gte-rerank-v2", "gte-rerank"),
        top_n_param="top_n",
        extra_body={"return_documents": True},
    ),
    "jina": RerankProvider(
        name="jina",
        endpoint="https://api.jina.ai/v1/rerank",
        api_key_env="JINA_API_KEY",
        default_model="jina-reranker-v3",
        recommended_models=(
            "jina-reranker-v3",
            "jina-reranker-v2-base-multilingual",
            "jina-reranker-v1-base-en",
            "jina-reranker-v1-turbo-en",
        ),
        top_n_param="top_n",
        extra_body={"return_documents": True},
    ),
    "voyage": RerankProvider(
        name="voyage",
        endpoint="https://api.voyageai.com/v1/rerank",
        api_key_env="VOYAGE_API_KEY",
        default_model="rerank-2.5",
        recommended_models=("rerank-2.5", "rerank-2.5-lite", "rerank-2", "rerank-2-lite", "rerank-1"),
        top_n_param="top_k",
    ),
    "cohere": RerankProvider(
        name="cohere",
        endpoint="https://api.cohere.ai/v2/rerank",
        api_key_env="COHERE_API_KEY",
        default_model="rerank-v4.0-fast",
        recommended_models=(
            "rerank-v4.0-fast",
            "rerank-v4.0-pro",
            "rerank-v3.5",
            "rerank-multilingual-v3.0",
            "rerank-english-v3.0",
        ),
        top_n_param="top_n",
        extra_body={"max_tokens_per_doc": 4096},
    ),
}


LOCAL_MODELS: tuple[str, ...] = (
    "BAAI/bge-reranker-v2-m3",
    "BAAI/bge-reranker-v2-gemma",
    "BAAI/bge-reranker-base",
    "BAAI/bge-reranker-large",
    "BAAI/bge-reranker-v2-minicpm-layerwise",
    "jinaai/jina-reranker-v2-base-multilingual",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
)

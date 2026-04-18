from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmbeddingProvider:
    name: str
    base_url: str
    api_key_env: str | None
    default_model: str
    recommended_models: tuple[str, ...]
    dimensions_param: str | None = None
    query_mode_param: str | None = None
    query_mode_value: str | None = None
    document_mode_value: str | None = None
    extra_body: dict[str, object] = field(default_factory=dict)


PROVIDERS: dict[str, EmbeddingProvider] = {
    "openai": EmbeddingProvider(
        name="openai",
        base_url="https://api.openai.com/v1/embeddings",
        api_key_env="OPENAI_API_KEY",
        default_model="text-embedding-3-small",
        recommended_models=("text-embedding-3-small", "text-embedding-3-large"),
        dimensions_param="dimensions",
        extra_body={"encoding_format": "float"},
    ),
    "dashscope": EmbeddingProvider(
        name="dashscope",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="text-embedding-v4",
        recommended_models=("text-embedding-v4", "text-embedding-v3"),
        dimensions_param="dimensions",
        extra_body={"encoding_format": "float"},
    ),
    "zhipu": EmbeddingProvider(
        name="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4/embeddings",
        api_key_env="ZHIPU_API_KEY",
        default_model="embedding-3",
        recommended_models=("embedding-3", "embedding-2"),
        dimensions_param="dimensions",
    ),
    "jina": EmbeddingProvider(
        name="jina",
        base_url="https://api.jina.ai/v1/embeddings",
        api_key_env="JINA_API_KEY",
        default_model="jina-embeddings-v3",
        recommended_models=("jina-embeddings-v3", "jina-embeddings-v4"),
        query_mode_param="task",
        query_mode_value="retrieval.query",
        document_mode_value="retrieval.passage",
        extra_body={"normalized": True, "embedding_type": "float"},
    ),
    "voyage": EmbeddingProvider(
        name="voyage",
        base_url="https://api.voyageai.com/v1/embeddings",
        api_key_env="VOYAGE_API_KEY",
        default_model="voyage-4-lite",
        recommended_models=("voyage-4-lite", "voyage-4", "voyage-4-large"),
        dimensions_param="output_dimension",
        query_mode_param="input_type",
        query_mode_value="query",
        document_mode_value="document",
        extra_body={"output_dtype": "float"},
    ),
    "ollama": EmbeddingProvider(
        name="ollama",
        base_url="http://127.0.0.1:11434/api/embed",
        api_key_env=None,
        default_model="bge-m3",
        recommended_models=("bge-m3", "nomic-embed-text", "mxbai-embed-large"),
        dimensions_param="dimensions",
    ),
}

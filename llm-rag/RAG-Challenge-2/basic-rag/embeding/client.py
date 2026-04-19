from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx
from providers import PROVIDERS, EmbeddingProvider


@dataclass
class EmbeddingResponse:
    """嵌入调用的响应结果数据类"""

    model: str
    vectors: list[list[float]]
    usage: dict[str, Any] | None = None


class BaseEmbeddingClient(ABC):
    """嵌入客户端抽象基类"""

    model: str

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> EmbeddingResponse:
        """为一组文档文本生成嵌入向量"""
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """为单个查询文本生成嵌入向量"""
        ...

    @abstractmethod
    async def batch_encode(
        self,
        texts: list[str],
        *,
        batch_size: int = 16,
        max_concurrency: int = 4,
        is_query: bool = False,
    ) -> list[list[float]]:
        """异步批量生成嵌入向量，支持并发控制"""
        ...


class BaseHttpEmbeddingClient(BaseEmbeddingClient):
    """基于 HTTP 的嵌入客户端基类，提供通用的批处理和网络请求构建逻辑"""

    def __init__(self, model: str, timeout: int = 60) -> None:
        self.model = model
        self.timeout = timeout

    def embed_documents(self, texts: list[str]) -> EmbeddingResponse:
        return self._embed(texts=texts, is_query=False)

    def embed_query(self, text: str) -> list[float]:
        response = self._embed(texts=[text], is_query=True)
        return response.vectors[0]

    async def batch_encode(
        self,
        texts: list[str],
        *,
        batch_size: int = 16,
        max_concurrency: int = 4,
        is_query: bool = False,
    ) -> list[list[float]]:
        if not texts:
            return []
        if batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")
        if max_concurrency <= 0:
            raise ValueError("max_concurrency 必须大于 0")

        chunks = [texts[index : index + batch_size] for index in range(0, len(texts), batch_size)]
        semaphore = asyncio.Semaphore(max_concurrency)

        async with httpx.AsyncClient(timeout=self.timeout) as client:

            async def encode_chunk(chunk: list[str]) -> list[list[float]]:
                async with semaphore:
                    response = await self._aembed(client, chunk, is_query)
                    return response.vectors

            results = await asyncio.gather(*(encode_chunk(chunk) for chunk in chunks))

        return [vector for chunk_vectors in results for vector in chunk_vectors]

    def _embed(self, texts: list[str], is_query: bool) -> EmbeddingResponse:
        if not texts:
            raise ValueError("texts 不能为空")
        payload = self._build_payload(texts=texts, is_query=is_query)
        body = self._post_json(payload)
        return self._parse_response(body)

    async def _aembed(
        self,
        client: httpx.AsyncClient,
        texts: list[str],
        is_query: bool,
    ) -> EmbeddingResponse:
        if not texts:
            raise ValueError("texts 不能为空")
        payload = self._build_payload(texts=texts, is_query=is_query)
        body = await self._apost_json(client, payload)
        return self._parse_response(body)

    @abstractmethod
    def _build_payload(self, texts: list[str], is_query: bool) -> dict[str, Any]: ...

    @abstractmethod
    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def _apost_json(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> dict[str, Any]: ...

    @abstractmethod
    def _parse_response(self, body: dict[str, Any]) -> EmbeddingResponse: ...


class RemoteEmbeddingClient(BaseHttpEmbeddingClient):
    """通用远程大模型嵌入客户端（兼容 OpenAI, 智谱, 阿里云等标准接口格式）"""

    def __init__(
        self,
        provider: EmbeddingProvider,
        model: str | None = None,
        dimensions: int | None = None,
        timeout: int = 400,
    ) -> None:
        super().__init__(model=model or provider.default_model, timeout=timeout)
        self.provider = provider
        self.dimensions = dimensions
        self.api_key = os.getenv(provider.api_key_env or "")
        if not self.api_key:
            raise ValueError(f"缺少环境变量: {provider.api_key_env}")

    def _build_payload(self, texts: list[str], is_query: bool) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
            **self.provider.extra_body,
        }
        if self.dimensions is not None and self.provider.dimensions_param:
            payload[self.provider.dimensions_param] = self.dimensions
        if self.provider.query_mode_param:
            payload[self.provider.query_mode_param] = (
                self.provider.query_mode_value if is_query else self.provider.document_mode_value
            )
        return payload

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self.provider.base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
            response.raise_for_status()
            return response.json()

    async def _apost_json(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await client.post(
            self.provider.base_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        response.raise_for_status()
        return response.json()

    def _parse_response(self, body: dict[str, Any]) -> EmbeddingResponse:
        vectors = [item["embedding"] for item in body["data"]]
        return EmbeddingResponse(model=body["model"], vectors=vectors, usage=body.get("usage"))


class OllamaEmbeddingClient(BaseHttpEmbeddingClient):
    """本地 Ollama 专用的嵌入客户端"""

    def __init__(
        self,
        provider: EmbeddingProvider,
        model: str | None = None,
        dimensions: int | None = None,
        timeout: int = 60,
    ) -> None:
        super().__init__(model=model or provider.default_model, timeout=timeout)
        self.provider = provider
        self.dimensions = dimensions

    def _build_payload(self, texts: list[str], is_query: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
            **self.provider.extra_body,
        }
        if self.dimensions is not None and self.provider.dimensions_param:
            payload[self.provider.dimensions_param] = self.dimensions
        if self.provider.query_mode_param:
            payload[self.provider.query_mode_param] = (
                self.provider.query_mode_value if is_query else self.provider.document_mode_value
            )
        return payload

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self.provider.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def _apost_json(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = await client.post(
            self.provider.base_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def _parse_response(self, body: dict[str, Any]) -> EmbeddingResponse:
        vectors = body.get("embeddings")
        if vectors is None:
            embedding = body.get("embedding")
            vectors = [embedding] if embedding is not None else []
        return EmbeddingResponse(
            model=body.get("model", self.model),
            vectors=vectors,
            usage={
                "total_duration": body.get("total_duration"),
                "load_duration": body.get("load_duration"),
                "prompt_eval_count": body.get("prompt_eval_count"),
            },
        )


def create_client(
    provider: str,
    model: str | None = None,
    dimensions: int | None = None,
) -> BaseEmbeddingClient:
    """
    客户端工厂方法，根据指定的提供商名称创建对应的嵌入客户端实例。
    """
    provider_info = PROVIDERS.get(provider)
    if provider_info is None:
        supported = ", ".join(PROVIDERS.keys())
        raise ValueError(f"不支持的提供商: {provider}。目前支持的提供商有: {supported}")

    if provider == "ollama":
        return OllamaEmbeddingClient(provider=provider_info, model=model, dimensions=dimensions)
    return RemoteEmbeddingClient(provider=provider_info, model=model, dimensions=dimensions)

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from providers import PROVIDERS, RerankProvider


@dataclass
class RerankItem:
    index: int
    score: float
    document: str | None = None


@dataclass
class RerankResponse:
    model: str
    results: list[RerankItem]
    usage: dict[str, Any] | None = None


class BaseRerankClient(ABC):
    model: str

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> RerankResponse: ...

    @abstractmethod
    async def batch_rerank(
        self,
        pairs: list[tuple[str, list[str]]],
        *,
        top_n: int | None = None,
        max_concurrency: int = 4,
    ) -> list[RerankResponse]: ...


class RemoteRerankClient(BaseRerankClient):
    def __init__(
        self,
        provider: RerankProvider,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.provider = provider
        self.model = model or provider.default_model
        self.timeout = timeout
        self.api_key = os.getenv(provider.api_key_env)
        if not self.api_key:
            raise ValueError(f"Missing environment variable: {provider.api_key_env}")

    def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> RerankResponse:
        payload = self._build_payload(query=query, documents=documents, top_n=top_n)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.provider.endpoint, json=payload, headers=self._headers())
            response.raise_for_status()
            return self._parse_response(response.json(), documents)

    async def batch_rerank(
        self,
        pairs: list[tuple[str, list[str]]],
        *,
        top_n: int | None = None,
        max_concurrency: int = 4,
    ) -> list[RerankResponse]:
        if not pairs:
            return []
        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be greater than 0")

        semaphore = asyncio.Semaphore(max_concurrency)
        results: list[RerankResponse | None] = [None] * len(pairs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async def worker(index: int, pair: tuple[str, list[str]]) -> None:
                query, documents = pair
                async with semaphore:
                    payload = self._build_payload(query=query, documents=documents, top_n=top_n)
                    response = await client.post(
                        self.provider.endpoint,
                        json=payload,
                        headers=self._headers(),
                    )
                    response.raise_for_status()
                    results[index] = self._parse_response(response.json(), documents)

            await asyncio.gather(*(worker(index, pair) for index, pair in enumerate(pairs)))

        return [item for item in results if item is not None]

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(
        self,
        *,
        query: str,
        documents: list[str],
        top_n: int | None,
    ) -> dict[str, Any]:
        if not query:
            raise ValueError("query must not be empty")
        if not documents:
            raise ValueError("documents must not be empty")

        if self.provider.name == "dashscope":
            payload: dict[str, Any] = {
                "model": self.model,
                "input": {"query": query, "documents": documents},
                "parameters": {**self.provider.extra_body},
            }
            if top_n is not None and self.provider.top_n_param:
                payload["parameters"][self.provider.top_n_param] = top_n
            return payload

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            **self.provider.extra_body,
        }
        if top_n is not None and self.provider.top_n_param:
            payload[self.provider.top_n_param] = top_n
        return payload

    def _parse_response(self, body: dict[str, Any], documents: list[str]) -> RerankResponse:
        if self.provider.name == "dashscope":
            output = body.get("output", {})
            results = [
                RerankItem(
                    index=item["index"],
                    score=float(item["relevance_score"]),
                    document=(item.get("document", {}) or {}).get("text"),
                )
                for item in output.get("results", [])
            ]
            return RerankResponse(
                model=body.get("model", self.model),
                results=results,
                usage=body.get("usage"),
            )

        if self.provider.name == "voyage":
            items = body.get("data", [])
            results = [
                RerankItem(
                    index=item["index"],
                    score=float(item["relevance_score"]),
                    document=documents[item["index"]] if 0 <= item["index"] < len(documents) else None,
                )
                for item in items
            ]
            return RerankResponse(
                model=body.get("model", self.model),
                results=results,
                usage=body.get("usage"),
            )

        if self.provider.name == "cohere":
            items = body.get("results", [])
            results = [
                RerankItem(
                    index=item["index"],
                    score=float(item["relevance_score"]),
                    document=documents[item["index"]] if 0 <= item["index"] < len(documents) else None,
                )
                for item in items
            ]
            return RerankResponse(
                model=self.model,
                results=results,
                usage=body.get("meta"),
            )

        items = body.get("results", [])
        results = [
            RerankItem(
                index=item["index"],
                score=float(item["relevance_score"]),
                document=((item.get("document") or {}).get("text") or documents[item["index"]]),
            )
            for item in items
        ]
        return RerankResponse(
            model=body.get("model", self.model),
            results=results,
            usage=body.get("usage"),
        )


def create_client(provider: str, model: str | None = None) -> BaseRerankClient:
    provider_info = PROVIDERS.get(provider)
    if provider_info is None:
        supported = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unsupported provider: {provider}. Supported providers: {supported}")
    return RemoteRerankClient(provider=provider_info, model=model)

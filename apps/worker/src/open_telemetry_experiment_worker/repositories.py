from abc import ABC, abstractmethod
from typing import Any

import httpx


class ExternalApiRepository(ABC):
    @abstractmethod
    async def get_fact(self) -> str: ...


class ServiceRepository(ABC):
    @abstractmethod
    async def process(self, text: str) -> dict[str, Any]: ...


class CallbackRepository(ABC):
    @abstractmethod
    async def send(self, callback_url: str, payload: dict[str, Any]) -> None: ...


class HttpxExternalApiRepository(ExternalApiRepository):
    def __init__(self, http_client: httpx.AsyncClient, base_url: str) -> None:
        self._http = http_client
        self._base_url = base_url

    async def get_fact(self) -> str:
        response = await self._http.get(f"{self._base_url}/facts/random")
        response.raise_for_status()
        return response.json()["text"]


class HttpxServiceRepository(ServiceRepository):
    def __init__(self, http_client: httpx.AsyncClient, base_url: str) -> None:
        self._http = http_client
        self._base_url = base_url

    async def process(self, text: str) -> dict[str, Any]:
        response = await self._http.post(f"{self._base_url}/process", json={"text": text})
        response.raise_for_status()
        return response.json()


class HttpxCallbackRepository(CallbackRepository):
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def send(self, callback_url: str, payload: dict[str, Any]) -> None:
        response = await self._http.post(callback_url, json=payload)
        response.raise_for_status()

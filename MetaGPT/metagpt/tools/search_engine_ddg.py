#!/usr/bin/env python

from __future__ import annotations

import asyncio
import json
from concurrent import futures
from typing import Literal, Optional, overload

from pydantic import BaseModel, ConfigDict
import asyncio, json
from concurrent import futures
from typing import Literal, Optional, overload
from pydantic import BaseModel, ConfigDict
from aiolimiter import AsyncLimiter
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from duckduckgo_search import DDGS
try:
    from duckduckgo_search import DDGS
except ImportError:
    raise ImportError(
        "To use this module, you should have the `duckduckgo_search` Python package installed. "
        "You can install it by running the command: `pip install -e.[search-ddg]`"
    )




# Custom exception for DuckDuckGo search errors
class DuckDuckGoSearchException(Exception):
    pass

class DDGAPIWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    loop: Optional[asyncio.AbstractEventLoop] = None
    executor: Optional[futures.Executor] = None
    proxy: Optional[str] = None
    rate_limiter: AsyncLimiter = AsyncLimiter(max_rate=1, time_period=1)

    @property
    def ddgs(self):
        return DDGS(proxies=self.proxy)

    @overload
    def run(self, query: str, max_results: int = 8, as_string: Literal[True] = True, focus: list[str] | None = None) -> str:
        ...

    @overload
    def run(self, query: str, max_results: int = 8, as_string: Literal[False] = False, focus: list[str] | None = None) -> list[dict[str, str]]:
        ...

    @retry(
        retry=retry_if_exception_type(DuckDuckGoSearchException),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(5),
        reraise=True
    )
    async def run(self, query: str, max_results: int = 8, as_string: bool = True) -> str | list[dict]:
        loop = self.loop or asyncio.get_event_loop()

        async with self.rate_limiter:
            try:
                future = loop.run_in_executor(self.executor, self._search_from_ddgs, query, max_results)
                search_results = await future
            except Exception as e:
                if 'Ratelimit' in str(e):
                    print(f"Rate limit hit for query: {query}. Retrying...")
                    raise DuckDuckGoSearchException("Rate limit exceeded") from e
                else:
                    print(f"An error occurred: {e}")
                    raise DuckDuckGoSearchException("An error occurred during search") from e

        if as_string:
            return json.dumps(search_results, ensure_ascii=False)
        return search_results

    def _search_from_ddgs(self, query: str, max_results: int):
        return [
            {"link": i["href"], "snippet": i["body"], "title": i["title"]}
            for (_, i) in zip(range(max_results), self.ddgs.text(query))
        ]

    @cached(ttl=300, cache=Cache.MEMORY, serializer=JsonSerializer())
    async def cached_run(self, query: str, max_results: int = 8, as_string: bool = True) -> str | list[dict]:
        """Cached version of the run method."""
        return await self.run(query, max_results, as_string)

if __name__ == "__main__":
    import fire
    api_wrapper = DDGAPIWrapper()
    fire.Fire(api_wrapper.cached_run)

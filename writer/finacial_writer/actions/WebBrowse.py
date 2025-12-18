#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from typing import Optional
from pydantic import BaseModel, ConfigDict
import aiohttp
from bs4 import BeautifulSoup
from metagpt.utils.parse_html import WebPage


class RequestsWrapper(BaseModel):
    """Requests Wrapper (Replaces SeleniumWrapper for non-browser scraping)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    proxy: Optional[str] = None
    
    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        async with aiohttp.ClientSession() as session:
            if urls:
                tasks = [self._scrape_website(session, u) for u in [url, *urls]]
                return await asyncio.gather(*tasks)
            return await self._scrape_website(session, url)

    async def _scrape_website(self, session, url):
        try:
            async with session.get(url, proxy=self.proxy, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    inner_text = soup.get_text(separator='\n', strip=True)
                    print(f"\n[Scraped Content from {url}]:\n{inner_text[:500]}...\n{'-'*50}")
                    return WebPage(inner_text=inner_text, html=html, url=url)
                else:
                    return WebPage(inner_text=f"Fail to load page: status {response.status}", html="", url=url)
        except Exception as e:
            return WebPage(inner_text=f"Fail to load page content for {e}", html="", url=url)


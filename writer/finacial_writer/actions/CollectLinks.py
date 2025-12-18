from __future__ import annotations
import asyncio
from typing import Any, Callable, Optional, Union
from pydantic import TypeAdapter, model_validator
from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.utils.common import OutputParser
from metagpt.utils.text import reduce_message_length

GET_JOB_PROMPT = """
根据需求文档，构建** 一个 **适合在网络上查找的信息搜索句子。注意现在是2025年，确保句子简洁明了，能够直接输入到网络搜索框中。你只需要输出信息搜索句子。
需求文档如下:
{instruction}
"""


RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n#TOPIC#\n{topic}"

SEARCH_TOPIC_PROMPT = """Please provide up to 4 necessary keywords related to your research topic for Google search. \
Your response must be in JSON format, for example: ["keyword1", "keyword2"]."""

SUMMARIZE_SEARCH_PROMPT = """### Requirements
1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
2. Provide up to {decomposition_nums} queries related to your research topic base on the search results.
3. Respond in the following JSON format: ["query1", "query2", "query3", ...].

### Search Result Information
{search_results}
"""

COLLECT_AND_RANKURLS_PROMPT = """### Topic
{topic}
### Query
{query}

### The online search results
{results}

### Requirements
Please remove irrelevant search results that are not related to the query or topic. Then, sort the remaining search results \
based on the link credibility. If two results have equal credibility, prioritize them based on the relevance. Provide the
ranked results' indices in JSON format, like [0, 1, 3, 4, ...], without including other words.
"""


class CollectLinks(Action):
    """Action class to collect links from a search engine."""

    name: str = "CollectLinks"
    i_context: Optional[str] = None
    desc: str = "Collect links from a search engine."
    search_func: Optional[Any] = None
    search_engine: Optional[SearchEngine] = None
    rank_func: Optional[Callable[[list[str]], None]] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.search_engine is None:
            self.search_engine = SearchEngine.from_search_config(self.config.search, proxy=self.config.proxy)
        return self

    async def run(
        self,
        instruction: str,
        decomposition_nums: int = 2,
        url_per_query: int = 4,
        system_text: str | None = None,
    ) -> dict[str, list[str]]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            decomposition_nums: The number of search questions to generate.
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        prompt = GET_JOB_PROMPT.format(instruction=instruction)
        topic = await self._aask(prompt)
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        keywords = await self._aask(SEARCH_TOPIC_PROMPT, [system_text])
        try:
            keywords = OutputParser.extract_struct(keywords, list)
            keywords = TypeAdapter(list[str]).validate_python(keywords)
        except Exception as e:
            logger.exception(f"fail to get keywords related to the research topic '{topic}' for {e}")
            keywords = [topic]
        results = await asyncio.gather(*(self.search_engine.run(i, as_string=False) for i in keywords))

        def gen_msg():
            while True:
                search_results = "\n".join(
                    f"#### Keyword: {i}\n Search Result: {j}\n" for (i, j) in zip(keywords, results)
                )
                prompt = SUMMARIZE_SEARCH_PROMPT.format(
                    decomposition_nums=decomposition_nums, search_results=search_results
                )
                yield prompt
                remove = max(results, key=len)
                remove.pop()
                if len(remove) == 0:
                    break

        model_name = config.llm.model
        prompt = reduce_message_length(gen_msg(), model_name, system_text, config.llm.max_token)
        logger.debug(prompt)
        queries = await self._aask(prompt, [system_text])
        try:
            queries = OutputParser.extract_struct(queries, list)
            queries = TypeAdapter(list[str]).validate_python(queries)
        except Exception as e:
            logger.exception(f"fail to break down the research question due to {e}")
            queries = keywords
        ret = {}
        for query in queries:
            ret[query] = await self._search_and_rank_urls(topic, query, url_per_query)
        return topic,ret

    async def _search_and_rank_urls(self, topic: str, query: str, num_results: int = 4) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect.

        Returns:
            A list of ranked URLs.
        """
        max_results = max(num_results * 2, 6)
        results = await self.search_engine.run(query, max_results=max_results, as_string=False)
        print(f"\n[Search Results for '{query}']: {results}\n")
        if len(results) == 0:
            return []
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results)
        logger.debug(prompt)
        indices = await self._aask(prompt)
        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]


# async def main():
#     collector = CollectLinks()
#     topic, links = await collector.run(
#         instruction="收集2023年新能源汽车行业统计数据",
#         decomposition_nums=3,
#         url_per_query=5
#     )
#     print(topic, links)

# asyncio.run(main())

from typing import Optional

import pydantic
from pydantic import model_validator

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.tools.search_engine import SearchEngine

SEARCH_AND_SUMMARIZE_SYSTEM = """### 要求
1. 请基于参考信息回答问题。不要包含与对话无关的文本。
- 上下文仅供参考。如果与用户的搜索请求无关，请减少其引用和使用。
2. 回复应优雅、清晰、不重复、行文流畅，长度适中。

### 对话历史（示例）
A:2024年3月，OpenAI发布了GPT-4，这是一个具有革命性的多模态AI模型，能够处理和理解文本、图像、音频、视频等多种类型的信息。GPT-4的出现标志着AI正式进入“多模态”时代，极大地扩展了AI的应用场景，如客户服务、教育和医疗等领域。谷歌在2024年末发布了Gemini系列模型，展示了其在多模态AI领域的雄心壮志。Gemini不仅能够理解多种类型的信息，还能生成图像、音频、视频和代码，预示着谷歌将在AI领域与OpenAI展开激烈竞争。

### 当前问题（示例）
A:返回有关人工智能领域的底层市场逻辑

### 当前回复（示例）
多模态能力成为竞争壁垒：GPT-4、Gemini等模型的迭代表明，AI从单一模态（文本）向多模态（文本、图像、音频、视频）的演进是技术发展的必然方向。这种能力扩展直接拓宽了AI的应用边界（如医疗影像分析、跨媒体内容生成），推动市场从工具型AI向通用型AI过渡。
"""

SEARCH_AND_SUMMARIZE_SYSTEM_EN_US = SEARCH_AND_SUMMARIZE_SYSTEM.format(LANG="zh-cn")

SEARCH_AND_SUMMARIZE_PROMPT = """
### Reference Information
{CONTEXT}

### Dialogue History
{QUERY_HISTORY}
{QUERY}

### Current Question
{QUERY}

### Current Reply: Based on the information, please write the reply to the Question

"""


class SearchAndSummarize(Action):
    name: str = ""
    content: Optional[str] = None
    search_engine: SearchEngine = None
    result: str = ""

    @model_validator(mode="after")
    def validate_search_engine(self):
        if self.search_engine is None:
            try:
                config = self.config
                search_engine = SearchEngine.from_search_config(config.search, proxy=config.proxy)
            except pydantic.ValidationError:
                search_engine = None

            self.search_engine = search_engine
        return self

    async def run(self, context: list[Message], system_text=SEARCH_AND_SUMMARIZE_SYSTEM) -> str:
        if self.search_engine is None:
            logger.warning("Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature")
            return ""

        query = context[-1].content
        # logger.debug(query)
        rsp = await self.search_engine.run(query)
        self.result = rsp
        if not rsp:
            logger.error("empty rsp...")
            return ""
        logger.info(rsp)

        system_prompt = [system_text]

        prompt = SEARCH_AND_SUMMARIZE_PROMPT.format(
            ROLE=self.prefix,
            CONTEXT=rsp,
            QUERY_HISTORY="\n".join([str(i) for i in context[:-1]]),
            QUERY=str(context[-1]),
        )
        result = await self._aask(prompt, system_prompt)
        logger.debug(prompt)
        logger.debug(result)
        return result

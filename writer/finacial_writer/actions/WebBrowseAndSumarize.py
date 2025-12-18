from typing import Annotated, Any, Callable, Coroutine, Optional, Union, overload
from metagpt.actions import Action
from pydantic import BaseModel, ConfigDict, Field, model_validator
from metagpt.logs import logger
from metagpt.utils.text import generate_prompt_chunk
from metagpt.configs.browser_config import BrowserConfig
from metagpt.utils.parse_html import WebPage
from finacial_writer.actions.WebBrowse import RequestsWrapper
from pathlib import Path

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

WEB_BROWSE_AND_SUMMARIZE_PROMPT = """### Requirements
1. Utilize the text in the "Reference Information" section to respond to the question "{query}".
2. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
3. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
4. Include all relevant factual information, numbers, statistics, etc.

### Reference Information
{content}
"""


class WebBrowserEngine(BaseModel):
    """Web Browser Engine for Automated Browsing.

    This class manages browser automation configurations, supporting Playwright, Selenium, or custom implementations.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    run_func: Annotated[
        Optional[Callable[..., Coroutine[Any, Any, Union[WebPage, list[WebPage]]]]],
        Field(exclude=True),
    ] = None
    proxy: Optional[str] = None
    executable_path: Optional[str] = None  

    @model_validator(mode="after")
    def validate_extra(self):
        """Validates extra configuration data after model initialization."""
        data = self.model_dump(exclude={"engine"}, exclude_none=True, exclude_defaults=True)
        if self.model_extra:
            data.update(self.model_extra)
        self._process_extra(**data)
        return self

    def _process_extra(self, **kwargs):
        run_func = RequestsWrapper(
            **kwargs).run
        self.run_func = run_func

    @classmethod
    def from_browser_config(cls, config: BrowserConfig, **kwargs):
        """Creates a WebBrowserEngine instance from a BrowserConfig object."""
        data = config.model_dump()
        return cls(**data, **kwargs)

    @overload
    async def run(self, url: str) -> WebPage:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[WebPage]:
        ...

    async def run(self, url: str, *urls: str) ->  Union[WebPage, list[WebPage]]:
        """Runs the browser engine to load web pages."""
        return await self.run_func(url, *urls)

class WebBrowseAndSummarize(Action):
    """Action class to explore the web and provide summaries of articles and webpages."""

    name: str = "WebBrowseAndSummarize"
    i_context: Optional[str] = None
    desc: str = "Explore the web and provide summaries of articles and webpages."
    browse_func: Union[Callable[[list[str]], None], None] = None
    web_browser_engine: Optional[WebBrowserEngine] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.web_browser_engine is None:
            self.web_browser_engine = WebBrowserEngine.from_browser_config(
                self.config.browser,
                browse_func=self.browse_func,
                proxy=self.config.proxy,
            )
        return self
    async def run(
        self,
        url: str,
        *urls: str,
        query: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> dict[str, str]:
        """Run the action to browse the web and provide summaries.

        Args:
            url: The main URL to browse.
            urls: Additional URLs to browse.
            query: The research question.
            system_text: The system text.

        Returns:
            A dictionary containing the URLs as keys and their summaries as values.
        """
        contents = await self.web_browser_engine.run(url, *urls)
        if not urls:
            contents = [contents]
        summaries = {}
        prompt_template = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content="{}")
        for u, content in zip([url, *urls], contents):
            content = content.inner_text
            print("!!!" + content)
            chunk_summaries = []
            for prompt in generate_prompt_chunk(content, prompt_template, self.llm.model, system_text, 4096):
                logger.debug(prompt)
                summary = await self._aask(prompt, [system_text])
                print(f"Summary chunk: {summary}")
                if summary == "Not relevant.":
                    continue
                chunk_summaries.append(summary)

            if not chunk_summaries:
                summaries[u] = None
                continue

            if len(chunk_summaries) == 1:
                summaries[u] = chunk_summaries[0]
                continue

            content = "\n".join(chunk_summaries)
            prompt = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content=content)
            summary = await self._aask(prompt, [system_text])
            summaries[u] = summary
        return summaries
    
class SaveResearch(Action):
    """Action class to conduct research and generate a research report."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _save_file(self, file_path: Path, content: str):
        """Save content to the specified file path."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Write the content to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.write(content)
        print(f"File saved to {file_path}")
        
    async def run(
        self,
        topic: str,
        content: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        path = self.config.project_path / 'docs' / 'summaries.md'
        self._save_file(path, content)
        return content

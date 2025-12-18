import asyncio
from pydantic import BaseModel
from finacial_writer.actions.WebBrowseAndSumarize import WebBrowseAndSummarize, SaveResearch
from finacial_writer.actions.CollectLinks import CollectLinks
from metagpt.actions import Action
from metagpt.actions.research import get_research_system_text
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from finacial_writer.actions.WriteRequirements import WriteRequirements

class Report(BaseModel):
    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""


class Researcher(Role):
    name: str = "David"
    profile: str = "Researcher"
    goal: str = "Gather information and conduct research"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "zh-cn"
    enable_concurrency: bool = True

    def __init__(self, decomposition_nums: int = 2, url_per_query: int = 2, **kwargs):
        super().__init__(**kwargs)
        # self._watch([WriteRequirements])
        self.decomposition_nums = decomposition_nums
        self.url_per_query = url_per_query
        self.set_actions([CollectLinks, WebBrowseAndSummarize,SaveResearch])
        self._set_react_mode(RoleReactMode.BY_ORDER.value, len(self.actions))
        
    async def _act(self) -> Message:
        # 记录日志，输出当前设置和要执行的任务
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # 获取要执行的任务
        todo = self.rc.todo
        # 从内存中获取消息
        msg = self.rc.memory.get(k=1)[0]
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            topic = msg.content

        research_system_text = self.research_system_text(topic, todo)
        if isinstance(todo, CollectLinks):
            topic, links = await todo.run(topic, self.decomposition_nums, self.url_per_query)
            ret = Message(
                content="", instruct_content=Report(topic=topic, links=links), role=self.profile, cause_by=todo
            )
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (
                todo.run(*url, query=query, system_text=research_system_text) for (query, url) in links.items() if url
            )
            if self.enable_concurrency:
                summaries = await asyncio.gather(*todos)
            else:
                summaries = [await i for i in todos]
            summaries = list((url, summary) for i in summaries for (url, summary) in i.items() if summary)
            ret = Message(
                content="", instruct_content=Report(topic=topic, summaries=summaries), role=self.profile, cause_by=todo
            )
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(f"url: {url}\nsummary: \n{summary}" for (url, summary) in summaries)
            content = await self.rc.todo.run(topic, summary_text, system_text=research_system_text)
            
            if not content:
                content = "No content available"
        
            ret = Message(
                content=content,
                # instruct_content=Report(topic=topic, content=content),
                # instruct_content=content,
                role=self.profile,
                cause_by=self.rc.todo,
            )
        self.rc.memory.add(ret)
        return ret

    def research_system_text(self, topic, current_task: Action) -> str:
        """BACKWARD compatible
        This allows sub-class able to define its own system prompt based on topic.
        return the previous implementation to have backward compatible
        Args:
            topic:
            language:

        Returns: str
        """
        return get_research_system_text(topic, self.language)

    async def react(self) -> Message:
        msg = await super().react()
        return msg


if __name__ == "__main__":
    import fire

    async def main(topic: str = "人工智能行业的相关数据", language: str = "zh-cn", enable_concurrency: bool = True):
        role = Researcher(language=language, enable_concurrency=enable_concurrency)
        await role.run(topic)

    fire.Fire(main)

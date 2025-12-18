from metagpt.actions import Action
from pathlib import Path

class HumanReview(Action):
    name: str = "ModifyReport"
    PROMPT_TEMPLATE: str = """
    请检查提供的行业报告，并给出一个关键的评论或反馈:
    {content}
    """
    
    async def run(self, instruction: str):
        content = instruction
        prompt = self.PROMPT_TEMPLATE.format(content = content)
        rsp = await self._aask(prompt)
        return rsp

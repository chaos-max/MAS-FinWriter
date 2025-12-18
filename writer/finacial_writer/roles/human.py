from metagpt.roles.role import Role
from finacial_writer.actions.HumanModify import HumanModify 
from finacial_writer.actions.HumanReview import HumanReview
from metagpt.schema import Message
from metagpt.logs import logger

class HumanExaminer(Role):
    name: str = "Final-Examiner"
    profile: str = "Final-Examiner"
    goal: str = "Modify the document according to the review"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([HumanReview])
        self.set_actions([HumanModify])
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg
    
    
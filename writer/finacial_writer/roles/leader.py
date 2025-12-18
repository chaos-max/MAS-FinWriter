import asyncio
import fire
from finacial_writer.actions.PrepareDocuments import PrepareDocuments
from finacial_writer.actions.WriteRequirements import WriteRequirements
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.roles.role import Role, RoleReactMode
from metagpt.actions import UserRequirement

class Leader(Role):
    name: str = "Alice"
    profile: str = "Leader"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement])
        self.set_actions([PrepareDocuments,WriteRequirements])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # By choosing the Action by order under the hood
        # todo will be first SimpleWriteCode() then SimpleRunCode()
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg
    
# def main(msg="写一份人工智能行业的金融报告"):
#     role = Leader()
#     logger.info(msg)
#     result = asyncio.run(role.run(msg))
#     logger.info(result)

# if __name__ == "__main__":
#     fire.Fire(main)
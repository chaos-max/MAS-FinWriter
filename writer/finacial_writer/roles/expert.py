from metagpt.roles.role import Role
from finacial_writer.actions.RagFix import RagFix
from finacial_writer.actions.FindFileAndDraw import FindFileAndDraw
class Expert(Role):
    name: str = "Expert"
    profile: str = "Expert"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([FindFileAndDraw(Filename = '东方财富概念版块')])
        self.set_actions([RagFix])

    
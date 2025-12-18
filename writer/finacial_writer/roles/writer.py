from finacial_writer.actions.WriterReport import WriteReport
from metagpt.roles.role import Role
from finacial_writer.actions.RagFix import RagFix
from finacial_writer.actions.WebBrowseAndSumarize import SaveResearch
class Writer(Role):
    name: str = "James"
    profile: str = "Writer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([RagFix])
        # self._watch([SaveResearch])
        self.set_actions([WriteReport])
    
    
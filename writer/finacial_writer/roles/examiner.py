from finacial_writer.actions.WriterReport import WriteReport
from metagpt.roles.role import Role
from finacial_writer.actions.ModifyReport import ModifyReport

class Examiner(Role):
    name: str = "Initial-Examiner"
    profile: str = "Initial-Examiner"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([WriteReport])
        self.set_actions([ModifyReport])
    
    
from metagpt.roles.role import Role
from finacial_writer.actions.ModifyReport import ModifyReport
from finacial_writer.actions.HumanReview import HumanReview
from finacial_writer.actions.HumanModify import HumanModify
class Reviewer(Role):
    name: str = "Reviewer"
    profile: str = "HumanReviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ModifyReport,HumanModify])
        self.set_actions([HumanReview])

    
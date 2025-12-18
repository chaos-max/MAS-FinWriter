from metagpt.roles.role import Role, RoleReactMode
from finacial_writer.actions.FindFileAndDraw import FindFileAndDraw
from finacial_writer.actions.WebBrowseAndSumarize import SaveResearch
class Drawer(Role):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the Drawer.
        profile (str): Role profile, default is 'Drawer'.
        goal (str): Primary goal or responsibility of the drawer.
        constraints (str): Constraints or guidelines for the drawer.
    """

    name: str = "Simon"
    profile: str = "Drawer"
    goal: str = "create clear, insightful, and interactive visualizations to support data-driven decisions"
    constraints: str = (
        "ensure the visualizations are intuitive, visually appealing, and accessible to the target audience. "
        "Use appropriate visualization tools and libraries like matplotlib, seaborn, or plotly."
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([SaveResearch])
        self.set_actions([FindFileAndDraw(Filename = '东方财富概念版块')])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

from pathlib import Path
from typing import Optional

from metagpt.actions import Action


class PrepareDocuments(Action):
    """PrepareDocuments Action: initialize project folder and add new requirements to a custom file path."""

    PROMPT_TEMPLATE: str = """
    为{instruction}行业研究报告的文件夹取个尽可能简短的名字,注意现在是2025年,仅返回名字即可
    """
    name: str = "PrepareDocuments"
    i_context: Optional[str] = None

    @property
    def config(self):
        return self.context.config

    def _init_project_folder(self, name: str):
        """Initialize the project folder."""
        
        path = Path(__file__).parent.parent.parent / "output" / name
        # Ensure the folder exists
        if not path.exists():
            path.mkdir(parents=True)
        self.config.project_path = path

    def _save_file(self, file_path: Path, content: str):
        """Save content to the specified file path."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.write(content)
        print(f"File saved to {file_path}")

    async def run(self, instruct_content: str) -> str:
        """Create and initialize the workspace folder, and save the requirements."""
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruct_content)
        rsp = await self._aask(prompt)
        self._init_project_folder(rsp)

        # Define the custom file path for saving requirements
        custom_path = self.config.project_path / 'docs' / 'input.txt'

        # Save the requirements to the custom path
        self._save_file(custom_path, instruct_content)

        # Return the action output
        return instruct_content

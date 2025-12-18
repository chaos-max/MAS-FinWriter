from metagpt.actions import Action
from pathlib import Path

class HumanModify(Action):
    name: str = "ModifyReport"
    PROMPT_TEMPLATE: str = """
    请根据需求修改报告内容,仅输出修改后的报告即可。    

    ### 需求
    {prd}

    ### 报告内容
    {content}
    """
    def _save_file(self, file_path: Path, content: str):
        """Save content to the specified file path."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.write(content)
        print(f"File saved to {file_path}")
    
    def _read_file(self, file_path: Path) -> str:
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    
    async def run(self, context: str):
        prd = context
        content = self._read_file(self.config.project_path / 'docs' / 'report.md')
        prompt = self.PROMPT_TEMPLATE.format(prd=prd, content = content)
        rsp = await self._aask(prompt)
        path = self.config.project_path / 'docs' / 'modify_report.md'
        self._save_file(path, rsp)
        return rsp
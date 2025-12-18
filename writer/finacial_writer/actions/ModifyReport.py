from metagpt.actions import Action
from pathlib import Path

class ModifyReport(Action):
    name: str = "ModifyReport"
    PROMPT_TEMPLATE: str = """
请根据需求文档和六个指标修改报告内容,仅输出修改后的报告完整版即可
- 注意保留原有的图片链接,不要编撰新的图片链接
- 尽量使用原始文本蕴含的内容，不要杜撰新的领域内容
- 注意在报告结尾保留并整合参考资料和链接 
- 输出长度要求：不少于原报告的150%
- 保持原有的研报结构和框架

### 指标	
逻辑性	内容是否结构清晰、论证严谨？ 改进例子:明确标题层级,修改段落逻辑,使其清晰且不重复。
客观性	是否避免了主观倾向，有充分证据？改进例子:丰富案例,数据标注详细。
洞察力	有无深入分析，提供独特视角？ 改进例子:深入技术细节,进行深度探讨。
数据质量	数据是否权威、最新？ 改进例子:增加数据来源和更新时间。
表达力	图表是否帮助理解？阅读是否流畅？ 改进例子:对数据密度过高的段落增加可视化摘要。
结论性	是否明确回答了“所以我们该怎么办”？ 改进例子:细化投资者类型,并针对不同类型的投资者提出具体建议。

### 需求文档
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
    
    async def run(self, instruction: str):
        prd = self._read_file(self.config.project_path / 'docs' / 'requirements.md')
        content = self._read_file(self.config.project_path / 'docs' / 'initial_report.md')
        prompt = self.PROMPT_TEMPLATE.format(prd=prd, content = content)
        rsp = await self._aask(prompt)
        path = self.config.project_path / 'docs' / 'report.md'
        self._save_file(path, rsp)
        return rsp

from metagpt.actions import Action
from pathlib import Path
import re

class WriteRequirements(Action):
    name: str = "WriteRequirements"
    PROMPT_TEMPLATE: str = """
# Requirements
请根据以下需求编写详细的产品需求文档，内容应基于 {instruction} 行业，要求如下:
1. 请基于{instruction}行业的分析来调整内容。
2. 仅输出产品需求文档，无需其他说明。
3. 以下是产品需求文档的结构，请根据要求填写：
4. 无需以markdown格式返回

    1.语言: "zh_cn"
    2.原始需求: "编写一份详细的行业分析报告，涵盖某个行业的定义、市场分析、竞争态势和未来发展趋势。"
    3.目标:
        在这个部分,你应给出报告的目标和预期结果。
        例如:
        - 提供全面的某个行业状况分析，包括市场结构、技术发展趋势和政策环境等指标。
    4.用户故事:
        在这个部分,你应列出具体的用户角色及其需求，以便于从不同角度理解报告对用户的价值。
        例如:
        - 作为投资经理，我希望能快速了解某个行业和市场的状况，以便做出投资决策。
    5.竞争分析:
        在这个部分,你应评估报告撰写行业内的主要竞争者，分析它们撰写的报告的优势和不足。
        例如:
        - 竞争对手A: 提供全面的行业数据分析，但缺乏对行业趋势的深度洞察。
    6.需求分析: 
        在这个部分,你应明晰报告应为决策者提供明确的建议和洞察，以支持其在 {instruction} 行业中的战略决策。
    7.需求池:
        在这个部分,你应列出报告中必须完成的需求和优先级，确保内容的完整性和重要性。
        例如:
        - P0: 提供某个行业状况的详细分析，包括市场结构、技术发展趋势和政策环境。
    """
    
    @staticmethod
    def parse_text(rsp):
        pattern = r"```markdown(.*)``"
        match = re.search(pattern, rsp, re.DOTALL)
        text = match.group(1) if match else rsp
        return text
    
    def _save_file(self, file_path: Path, content: str):
        """Save content to the specified file path."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with file_path.open("w", encoding="utf-8") as file:
            file.write(content)
        print(f"File saved to {file_path}")
    
    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        rsp = await self._aask(prompt)
        rsp = WriteRequirements.parse_text(rsp)
        path = self.config.project_path / 'docs' / 'requirements.md'
        self._save_file(path, rsp)
        return rsp

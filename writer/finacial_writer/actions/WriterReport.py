from metagpt.actions import Action
from pathlib import Path
import os
import glob

class WriteReport(Action):
    name: str = "WriteReport"
    PROMPT_TEMPLATE_SUMMARY: str = """
### Reference Information
{content}

### Requirements
请使用上述提供的信息和主题{topic},完成下面两部分内容,直接输出内容即可:

#### ** 封面**
- 标题格式:“年份+国家/地区+行业名称+研究报告”(例:《2024年中国人工智能行业研究报告》)
- 底部添加免责声明:“本报告数据来源于公开资料,仅作参考,不构成任何投资建议。”

#### ** 摘要**
- 用简洁语言提炼3-5条核心结论,包括:
  - 行业当前发展阶段(萌芽/成长/成熟/衰退)
  - 未来3年关键趋势(技术、政策、市场)
  - 潜在风险与机会提示

"""

    PROMPT_TEMPLATE_1: str ="""
### Reference Information
{content}

### Requirements
请针对 "{topic}" 提供详细的行业研究报告的行业概述章节内容，使用上述提供的信息。
报告必须符合以下要求：

- 重点直接针对所选主题。
- 确保报告结构严谨、深入浅出，并纳入相关事实和数据。
- 以直观的方式呈现数据和研究结果，并酌情使用特色对比表格。
- 报告字数不得少于 1,500 字，格式应使用 Markdown 语法，并遵循 APA 样式指南。
- 在报告末尾以 APA 格式列出所有资料来源的 URL。
- 仅需包括如下两部分内容:

#### ** 行业概述**
- 定义行业范围(说明细分领域和边界)
- 发展历程(时间轴形式,标注里程碑事件)
- 说明⾏业应⽤场景
- 主要国家政策环境对比(列举直接影响行业的国家政策,并具体说明相关的政策内容)
- 相关行业指数的图片在相对路径{path},根据需要使用相对路径进行引用

"""

    PROMPT_TEMPLATE_2: str ="""
### Reference Information
{content}

### Requirements
请针对 "{topic}" 提供详细的行业研究报告的市场分析章节内容,使用上述提供的信息。
报告必须符合以下要求：

- 重点直接针对所选主题。
- 确保报告结构严谨、深入浅出，并纳入相关事实和数据。
- 以直观的方式呈现数据和研究结果，并酌情使用特色对比表格。
- 报告字数不得少于 1,500 字，格式应使用 Markdown 语法，并遵循 APA 样式指南。
- 在报告末尾以 APA 格式列出所有资料来源的 URL。
- 仅需包括如下部分内容:

#### ** 市场分析**
- 市场规模:提供历史数据和预测数据(单位:亿元/美元),标注数据来源
- 供需分析:用“供给端-需求端”对比框架,各列3点
- 区域竞争格局:列出全球各个地区的优势领域和代表企业,分析竞争壁垒
- 国内竞争格局:列出中国各个地区的优势领域和代表企业,分析竞争壁垒


"""

    PROMPT_TEMPLATE_3: str ="""
### Reference Information
{content}

### Requirements
请针对以下主题提供一份详细的行业研究报告： “{topic}"，使用上述提供的信息。
报告必须符合以下要求：

- 重点直接针对所选主题。
- 确保报告结构严谨、深入浅出，并纳入相关事实和数据。
- 以直观的方式呈现数据和研究结果，并酌情使用特色对比表格。
- 报告字数不得少于 1,500 字，格式应使用 Markdown 语法，并遵循 APA 样式指南。
- 在报告末尾以 APA 格式列出所有资料来源的 URL。
- 仅需包括如下两部分内容:

##### ** 未来展望**
- 短期(1-3年):需针对各个细分领域量化(如“2025年xx领域渗透率预计达XX%”)
- 长期(5-10年):结合技术突破、国际竞争等维度

##### ** 投资建议**
- 按风险偏好分类(保守型/平衡型/激进型),各推荐1-2个方向,最好具体到公司,并说明理由
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

    def get_png_files(self, directory, relative_to):
        absolute_paths = glob.glob(os.path.join(directory, "*.png"))

        relative_paths = [os.path.relpath(path, relative_to) for path in absolute_paths]

        return relative_paths

    
    async def run(self, instruction: str):
        topic = self._read_file(self.config.project_path / 'docs' / 'input.txt')
        content = self._read_file(self.config.project_path / 'docs' / 'processed_summaries.md')
        # content = self._read_file(self.config.project_path / 'docs' / 'summaries.md')
        
        directory_path = self.config.project_path / 'image'  
        report_path = self.config.project_path / 'docs' 
        png_files = self.get_png_files(directory_path , report_path)
        prompt1 = self.PROMPT_TEMPLATE_1.format(topic=topic, content = content, path = png_files)
        prompt2 = self.PROMPT_TEMPLATE_2.format(topic=topic, content = content)
        prompt3 = self.PROMPT_TEMPLATE_3.format(topic=topic, content = content)
        rsp = await self._aask(prompt1)
        rsp += await self._aask(prompt2)
        rsp += await self._aask(prompt3)
        prompt_summary = self.PROMPT_TEMPLATE_SUMMARY.format(topic=topic, content = rsp)
        rsp = await self._aask(prompt_summary) + rsp
        path = self.config.project_path / 'docs' / 'initial_report.md'
        self._save_file(path, rsp)
        return rsp

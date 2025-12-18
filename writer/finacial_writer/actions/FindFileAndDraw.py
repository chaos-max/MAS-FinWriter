from metagpt.actions import Action
from pathlib import Path
from metagpt.roles.di.data_interpreter import DataInterpreter
import re
import os
from metagpt.utils.recovery_util import save_history

class FindFileAndDraw(Action):
    name: str = "FindFile"
    INDUSTRY_FILE_SEARCH_REQ: str = """
    从下面的列表中提取所有与{instruction}有关的行业。
    要求:
    1.返回的行业**必须包含**在给出的列表中。
    2.以 JSON 格式提供结果列表，如 [Industry1,Industry2,Industry3]，不包括其他字词,至多返回10个。
    
    列表如下： 
    {content}
    """
    
    SALES_FORECAST_REQ: str = """
The dataset is {DATA_DIR}, which contains a series of filenames. 
Each file contains historical values for these features ('name', 'trade_date', 'pe', 'pb', 'total_mv') and potentially more information. 
Notice: The 'trade_date' field is in the format YYYYMMDD (e.g., 20240102), and should be converted to a datetime format.

For each file, extract the following time-related features:
- Year: Extract the year from the trade date.
- Month: Extract the month from the trade date.
- Day: Extract the day of the month from the trade date.

Plot the trend of relevant financial metrics (e.g. 'total_mv', or any other feature available in the file) over 'trade_date' for all files on the same graph.
The x-axis should represent 'trade_date', and the y-axis should represent the values of the selected metrics with unit '万元'
Please ensure that:
- The x-axis uses the datetime format.
- Each file's data is displayed on the same plot, with a different color or style to distinguish them.
- Include a legend with accurate labels corresponding to each file's name to make sure each file can be identified properly.
- Set font "SimHei". Do not use plt.rcParams to set fonts globally. Load the font file directly via FontProperties, with the font path as:font_path = "{FONT_PATH}".
- Use plt.subplots() to create a figure and axis object.

Save the plot under {SAVE_DIR}, and the filename should include "{Save_Filename}". 
**Important Notes:**
Use fig.savefig() to save the figure.
"""
    Filename: str
    def _read_file(self, file_path: Path):
        with open(file_path, 'r') as f:
            industries = [line.strip()[:-4] for line in f.readlines()]
            return industries
    def _read_input_file(self, file_path: Path):
        with open(file_path, 'r') as f:
            return f.read()
        
    def extract_and_add_prefix(self, text: str, prefix: str) -> list:
        # 正则表达式匹配文件名（假设文件名以 .csv 结尾）
        matches = re.findall(r'\[(.*?)\]', text,re.DOTALL)
        text = matches[0]
        text = [s.strip().strip('"').strip('\'') for s in text.split(",")]
        csv_files = [category + '.csv' for category in text]
        # 加上前缀路径
        full_paths = [f"{prefix}{file_name}" for file_name in csv_files]
        return full_paths


    async def run(self, instruction: str):
        instruction = self._read_input_file(self.config.project_path /'docs' / 'input.txt')
        # instruction = "煤炭" #测试代码
        
        # Use dynamic path resolution relative to the writer directory
        writer_root = Path(__file__).resolve().parents[2]
        name_path = writer_root / f'data/{self.Filename}/all_names.txt'
        
        # Resolve font path dynamically
        font_path = writer_root / 'SimHei.ttf'
        
        content = self._read_file(name_path)
        prompt = self.INDUSTRY_FILE_SEARCH_REQ.format(instruction=instruction,content = content)
        rsp = await self._aask(prompt)
        
        # Update prefix to use absolute path
        prefix = str(writer_root / f"data/{self.Filename}") + "/"
        
        # 提取文件名并加上前缀
        DATA_DIR = self.extract_and_add_prefix(rsp, prefix)

        SAVE_DIR = self.config.project_path /'image' 
        # SAVE_DIR = "/Users/ash/Desktop/毕业/writer/data" #测试代码
        os.makedirs(SAVE_DIR, exist_ok=True)
        mi = DataInterpreter()
        target_workspace = self.config.project_path / 'code'
        # mi.rc.work_dir = target_workspace
        
        await mi.run(self.SALES_FORECAST_REQ.format(DATA_DIR=DATA_DIR,SAVE_DIR=SAVE_DIR,Save_Filename=self.Filename, FONT_PATH=str(font_path)))
        save_history(role=mi, save_dir=str(target_workspace))
        return "已经绘制图片"
    

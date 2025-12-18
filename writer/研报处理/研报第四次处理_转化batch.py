import os
import glob
import json
from pathlib import Path
from tqdm import tqdm
# 假设你的文件存储在一个目录中
BASE_DIR = Path(__file__).resolve().parent.parent
directory = os.path.join(BASE_DIR, "data", "有效研报的章节数据")

output_directory = os.path.join(BASE_DIR, "data", "研报batch数据")

os.makedirs(output_directory, exist_ok=True)

txt_files = glob.glob(os.path.join(directory, "*.txt"))

for txt_file in tqdm(txt_files):
# 打开文件并读取所有行
    with open(txt_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    data = []
# 遍历每一行，将每一行作为一个句子添加到列表中
    custom_id_counter = 1
    for line in lines:
          # 每个文件从 request-1 开始
        # 创建一个字典，包含 custom_id、method、url 和 body 字段
        content = line.strip()
        if len(content) < 10:
            continue
        item = {
            "custom_id": f"request-{custom_id_counter}",
            "method": "POST",
            "url": "/v4/chat/completions",
            "body": {
                "model": "glm-4-flash",
                "messages": [
                    {"role": "system", "content": "你是一个句子分类器"},
                    {"role": "user", "content": 
                    f"""请判断以下句子是否可以提取出行业领域的因果关系。要求：
                        1. 如果句子中包含因果关系，直接返回输入的句子，无需返回其他内容
                        2. 如果句子中不包含因果关系,返回“无”
                        现在请判断：
                        句子：{line.strip()}
                        """
                    }
                ],
                "temperature": 0.1,
            }
        }
        custom_id_counter += 1
        data.append(item)
    file_path, file_name = os.path.split(txt_file)
    output_file_name = os.path.splitext(file_name)[0] + ".jsonl"
    output_file_path = os.path.join(output_directory, output_file_name)
        
        # 打开一个新的文件用于写入提取的内容
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for item in data:
            json.dump(item, output_file, ensure_ascii=False)
            output_file.write("\n")

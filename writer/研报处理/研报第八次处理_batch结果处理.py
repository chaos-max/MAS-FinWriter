import json
import os
import re
from rapidfuzz import fuzz
from tqdm import tqdm
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
input_directory = os.path.join(BASE_DIR, "data", "下载的batch数据")
output_directory = os.path.join(BASE_DIR, "data", "处理后的batch数据")
os.makedirs(output_directory, exist_ok=True)
# 获取目录下的所有 JSONL 文件
jsonl_files = [f for f in os.listdir(input_directory) if f.endswith(".jsonl")]

for jsonl_file in jsonl_files:
    jsonl_file = "batchoutput_0.jsonl"
    file_path = os.path.join(input_directory, jsonl_file)
    with open(file_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f) # 重新打开文件
    # 逐行读取 JSONL 文件
    with open(file_path, "r", encoding="utf-8") as inputfile:
        output_file = os.path.join(output_directory, jsonl_file)  # 处理后的输出文件
        unique_lines = []
        removed_lines = []
        for line in tqdm(inputfile, total=total_lines):     
            data = json.loads(line)  # 将 JSON 字符串转换为 Python 字典
            content = data["response"]["body"]["choices"][0]["message"]["content"]
            content = (re.sub(r"\s+", "", content)).rstrip("无")
            if(len(content) < 15) :
                continue
            if any(fuzz.ratio(content, existing) > 85 for existing in unique_lines):
                removed_lines.append(content)  # 记录被删除的 JSON 行
            else:
                unique_lines.append(content)
                
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in unique_lines)
        print(f"去重完成，保留 {len(unique_lines)} 条，删除 {len(removed_lines)} 条。")

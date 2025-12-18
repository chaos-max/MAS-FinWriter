# 统计研报章节出现次数
import os
import glob
import re
from pathlib import Path
from tqdm import tqdm
# 假设你的文件存储在一个目录中
BASE_DIR = Path(__file__).resolve().parent.parent
directory = os.path.join(BASE_DIR, "data", "研报数据")

# 定义节标题的正则表达式
section_pattern = re.compile(r'第[一二三四五六七八九十百千万]+节\s*([^\n]+)')

# 获取目录下所有 .txt 文件的路径
txt_files = glob.glob(os.path.join(directory, "*.txt"))

# 初始化统计结果
# 结构：{节标题: 出现次数}
section_count = {}

# 遍历每个 .txt 文件
for txt_file in tqdm(txt_files):
    # 打开文件并读取内容
    with open(txt_file, "r", encoding="utf-8") as file:
        content = file.read()

    # 查找所有节标题
    sections = section_pattern.findall(content)

    # 统计每一节的出现次数
    for section in sections:
        if section in section_count:
            section_count[section] += 1
        else:
            section_count[section] = 1

# 输出统计结果
for section, count in section_count.items():
    if count > 5000:
        print(f"节标题: {section}, 出现次数: {count}")
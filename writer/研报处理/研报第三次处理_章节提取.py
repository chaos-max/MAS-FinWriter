# 提取目标章节
import os
import glob
import re
from tqdm import tqdm
# 节标题: 释义, 出现次数: 5034
# 节标题: 公司简介和主要财务指标, 出现次数: 11574
# 节标题: 公司业务概要, 出现次数: 7319
# 节标题: 经营情况讨论与分析, 出现次数: 7338
# 节标题: 重要事项, 出现次数: 11685
# 节标题: 优先股相关情况, 出现次数: 11424
# 节标题: 董事、监事、高级管理人员和员工情况, 出现次数: 7314
# 节标题: 公司治理, 出现次数: 11620
# 节标题: 公司债券相关情况, 出现次数: 7599
# 节标题: 财务报告, 出现次数: 11820
# 节标题: 备查文件目录, 出现次数: 7278
# 节标题: 重要提示、目录和释义, 出现次数: 6509
# 节标题: 股份变动及股东情况, 出现次数: 8743

directory = "/Users/ash/Desktop/毕业/writer/data/研报数据"

output_directory = "/Users/ash/Desktop/毕业/writer/data/有效研报的章节数据"

# 确保输出目录存在
os.makedirs(output_directory, exist_ok=True)

# 定义节标题的正则表达式
section_pattern = re.compile(r'第[一二三四五六七八九十百千万]+节\s*([^\n]+)')

# 获取目录下所有 .txt 文件的路径
txt_files = glob.glob(os.path.join(directory, "*.txt"))

# 定义节标题的正则表达式
section_pattern = re.compile(r'第[一二三四五六七八九十百千万]+节\s*([^\n]+)\s*([\s\S]*?)(?=第[一二三四五六七八九十百千万]+节|$)')

# 目标节标题
target_sections = [
    "公司业务概要",
    "经营情况讨论与分析",
]
                   

# 遍历每个 .txt 文件

# 打开文件并读取内容
for txt_file in tqdm(txt_files):
    with open(txt_file, "r", encoding="utf-8") as file:
        content = file.read()

    # 查找所有节标题及其内容
    sections = section_pattern.findall(content)
    file_name = os.path.basename(txt_file)
    company_name = file_name.split("__")[1]  # 假设公司名称在文件名中的第二个部分

    # 初始化目标节内容
    target_content = None
    
    file_path, file_name = os.path.split(txt_file)
    # 创建输出文件的路径和文件名
    output_file_name = file_name
    output_file_path = os.path.join(output_directory, output_file_name)
    
    # 打开一个新的文件用于写入提取的内容
    
    # 遍历每一节
    for section in sections:
        section_title = section[0].strip()  # 节标题
        section_content = section[1].strip()  # 节内容
        # 如果找到目标节
        if section_title in target_sections:
            target_content = section_content
            target_content = re.sub(r'(\r\n|\r|\n)\s*(\r\n|\r|\n)+', '\n', target_content)
            target_content = re.sub(r'√适用□不适用', '', target_content)
            target_content = re.sub(r'□适用√不适用', '', target_content)
            target_content = target_content.replace("公司", company_name)
                
            with open(output_file_path, "a", encoding="utf-8") as output_file:
                output_file.write(section_title + "\n" + target_content + "\n")


# 定义分句的正则表达式（支持中文和英文标点）
sentence_pattern = re.compile(r'([。！？；.!?;])')

# 遍历每个 .txt 文件
txt_files = glob.glob(os.path.join(output_directory, "*.txt"))

for txt_file in tqdm(txt_files):
    with open(txt_file, "r", encoding="utf-8") as file:
        content = file.read()

    # 将多行内容合并为一行
    single_line_content = content.replace("\n", "").strip()

    # 按句号、问号、感叹号分句
    sentences = []
    temp_sentence = ""
    for char in single_line_content:
        temp_sentence += char
        if char in {"。", "！", "？"}:
            sentences.append(temp_sentence.strip())
            temp_sentence = ""
    # 添加最后一句（如果没有以标点结尾）
    if temp_sentence:
        sentences.append(temp_sentence.strip())

    # 将句子按每行一个句子的格式合并
    formatted_content = "\n".join(sentences)

    # 获取文件名（不带路径）
    file_name = os.path.basename(txt_file)
    # 定义输出文件路径
    output_file_path = os.path.join(output_directory, file_name)

    # 将处理后的内容写入新文件
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(formatted_content)
            
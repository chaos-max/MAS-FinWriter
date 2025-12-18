# -*- coding: utf-8 -*-
from openai import OpenAI
import os
import glob
#   api_type: "openai"  
#   model: "deepseek-chat"
#   base_url: 'https://api.deepseek.com/v1 '
#   api_key: 'sk-b560811e06964abaa9e6c152f6ff4cd7'
from pathlib import Path

client = OpenAI(api_key="", base_url="https://api.deepseek.com")

BASE_DIR = Path(__file__).resolve().parent.parent
directory = os.path.join(BASE_DIR, "data", "处理后的batch数据")

# 指定输出目录
output_directory = os.path.join(BASE_DIR, "data", "因果关系")

# 确保输出目录存在
os.makedirs(output_directory, exist_ok=True)

# 获取目录下所有 .txt 文件的路径
json_files = glob.glob(os.path.join(directory, "*.jsonl"))

import os

# 遍历每个 .txt 文件
for json_file in json_files:
    with open(json_file, "r", encoding="utf-8") as file:
        _, file_name = os.path.split(json_file)
        
        # 创建输出文件的路径和文件名
        output_file_name = file_name
        output_file_path = os.path.join(output_directory, output_file_name)
        
        # 初始化变量
        content_chunk = ""
        chunk_size_limit = 5000
        
        # 逐行读取文件
        for line in file:
            # 如果当前行加上已累积的内容超过限制，则处理当前累积的内容
            if len(content_chunk) + len(line) > chunk_size_limit:
                # 调用 API 处理内容
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": 
                        """
                            用户将提供给你一段内容，请你分析内容，并提取其中与行业有关的因果关系。
                            注意，应避免公司出现在因果关系中，而注重于和整个行业有关的因果关系提取。
                            输出需遵守以下的格式：
                            {
                            "industry": <行业>,
                            "cause and effect": <因果关系>
                            }
                        """},
                        {"role": "user", "content": content_chunk},
                    ],
                    stream=False
                )
                
                # 将结果追加写入输出文件
                with open(output_file_path, "a", encoding="utf-8") as output_file:
                    output_file.write(response.choices[0].message.content + "\n")  # 每个结果换行分隔
                
                # 重置累积的内容
                content_chunk = line
            else:
                # 累积当前行
                content_chunk += line.strip() + "\n"  # 每行后加换行符
        
        # 处理最后剩余的累积内容（如果有）
        if content_chunk:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 
                    """
                        用户将提供给你一段内容，请你分析内容，并提取其中与行业有关的因果关系。
                        注意，应避免公司出现在因果关系中，而注重于和整个行业有关的因果关系提取。
                        输出需遵守以下的格式：
                        {
                        "industry": <行业>,
                        "cause": <原因>,
                        "effect": <结果>
                        }
                    """},
                    {"role": "user", "content": content_chunk},
                ],
                stream=False
            )
            
            with open(output_file_path, "a", encoding="utf-8") as output_file:
                output_file.write(response.choices[0].message.content + "\n")
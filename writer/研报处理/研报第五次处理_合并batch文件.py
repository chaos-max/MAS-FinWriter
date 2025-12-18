import os
import glob
import json
from pathlib import Path
from tqdm import tqdm
# 输入目录（包含需要合并的 .jsonl 文件）
BASE_DIR = Path(__file__).resolve().parent.parent
input_directory = os.path.join(BASE_DIR, "data", "研报batch数据")
# 输出目录（存储合并后的文件）
output_directory = os.path.join(BASE_DIR, "data", "合并后的研报batch数据")

# 确保输出目录存在
os.makedirs(output_directory, exist_ok=True)

# 获取所有 .jsonl 文件
jsonl_files = glob.glob(os.path.join(input_directory, "*.jsonl"))

# 初始化变量
batch_size = 50000  # 每个文件的最大行数
current_batch = []  # 当前批次的 JSON 对象
file_count = 1      # 合并文件的计数器

# 遍历每个 .jsonl 文件
for jsonl_file in tqdm(jsonl_files):
    with open(jsonl_file, "r", encoding="utf-8") as file:
        for line in file:
            # 加载 JSON 对象
            item = json.loads(line.strip())
            current_batch.append(item)

            # 如果当前批次的行数达到 batch_size，写入文件
            if len(current_batch) >= batch_size:
                # 定义输出文件路径
                output_file_path = os.path.join(output_directory, f"merged_batch_{file_count}.jsonl")
                # 写入文件，并重置 custom_id
                with open(output_file_path, "w", encoding="utf-8") as output_file:
                    custom_id_counter = 1  # 每个文件从 request-1 开始
                    for item in current_batch:
                        item["custom_id"] = f"request-{custom_id_counter}"  # 更新 custom_id
                        custom_id_counter += 1  # 递增计数器
                        json.dump(item, output_file, ensure_ascii=False)
                        output_file.write("\n")
                # 重置当前批次
                current_batch = []
                file_count += 1

# 处理剩余的 JSON 对象（不足 batch_size 的部分）
if current_batch:
    output_file_path = os.path.join(output_directory, f"merged_batch_{file_count}.jsonl")
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        custom_id_counter = 1  # 每个文件从 request-1 开始
        for item in current_batch:
            item["custom_id"] = f"request-{custom_id_counter}"  # 更新 custom_id
            custom_id_counter += 1  # 递增计数器
            json.dump(item, output_file, ensure_ascii=False)
            output_file.write("\n")

print(f"合并完成，共生成 {file_count} 个文件。")
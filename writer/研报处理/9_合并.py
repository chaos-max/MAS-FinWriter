import os
import glob
from rapidfuzz import process, fuzz
from tqdm import tqdm

def read_json_files(folder_path):
    """读取文件夹下所有txt文件的内容"""
    json_files = glob.glob(os.path.join(folder_path, "*.jsonl"))
    lines = []
    
    print(f"🔍 发现 {len(json_files)} 个文本文件，开始读取...")
    for file in tqdm(json_files, desc="📂 读取文件", unit="file"):
        with open(file, "r", encoding="utf-8") as f:
            lines.extend([line.strip() for line in f if line.strip()])  # 去除空行
    
    print(f"📖 读取完成，共 {len(lines)} 行文本")
    return lines

def remove_duplicates(lines, threshold=90):
    """
    使用 rapidfuzz 去重文本
    :param texts: 文本列表
    :param threshold: 相似度阈值，默认90
    :return: 去重后的文本列表
    """
    unique_lines = []
    
    print(f"🔄 开始去重，共 {len(lines)} 行...")
    for line in tqdm(lines, desc="🚀 去重中", unit="line"):
        # 计算与当前去重列表中的相似度
        matches = process.extract(line, unique_lines, scorer=fuzz.ratio, score_cutoff=threshold)
        
        # 如果没有相似度超过阈值的，加入去重列表
        if not matches:
            unique_lines.append(line)
    
    print(f"✅ 去重完成，剩余 {len(unique_lines)} 条唯一行")
    return unique_lines

def merge_and_deduplicate_txt(folder_path, output_file, threshold=90):
    """合并所有 txt 文件并去重"""
    lines = read_json_files(folder_path)
    unique_lines = remove_duplicates(lines, threshold)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(unique_lines))  # 按行写入
    
    print(f"📁 处理完成！去重后文本已保存到 {output_file}")


# 使用示例
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
folder_path = os.path.join(BASE_DIR, "data", "处理后的batch数据")  # 替换成你的文件夹路径
output_file = os.path.join(BASE_DIR, "data", "merged_deduplicated.txt")
merge_and_deduplicate_txt(folder_path, output_file)

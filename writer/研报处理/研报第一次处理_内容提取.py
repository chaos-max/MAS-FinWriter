import json
import os
import glob
from pathlib import Path
from rapidfuzz import fuzz
from tqdm import tqdm
# 定义常量
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIRECTORY = os.path.join(BASE_DIR, "data", "原始研报数据")  # 原始研报数据目录
OUTPUT_DIRECTORY = os.path.join(BASE_DIR, "data", "研报数据")  # 提取后的研报数据目录
TARGET_SENTENCES = ["公司简介", "公司概要", "公司基本情况","经营情况"]  # 目标句子
SIMILARITY_THRESHOLD = 80  # 相似度阈值


def extract_text_from_reports(input_dir, output_dir):
    """
    从原始研报数据中提取 type 为 text 的内容，并保存到新的文件中。
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取目录下所有 .txt 文件的路径
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))

    # 遍历每个 .txt 文件
    for txt_file in tqdm(txt_files):
        # 打开文件并逐行读取
        with open(txt_file, "r", encoding="utf-8") as file:
            # 获取输入文件的路径和文件名
            _, file_name = os.path.split(txt_file)
            # 创建输出文件的路径和文件名
            output_file_path = os.path.join(output_dir, file_name)
            
            # 打开一个新的文件用于写入提取的内容
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                for line in file:
                    # 解析每一行 JSON 数据
                    try:
                        record = json.loads(line)
                        # 提取 type 为 text 的记录
                        if record and record.get("type") == "text":
                            # 将提取的内容写入新的文件
                            output_file.write(record.get("inside", "") + "\n")
                    except json.JSONDecodeError:
                        print(f"文件 '{txt_file}' 中存在无效的 JSON 数据，跳过该行。")


def filter_reports_by_sentences(directory, target_sentences, similarity_threshold):
    """
    过滤研报数据，删除不包含目标句子的文件。
    """
    # 获取目录下所有 .txt 文件的路径
    txt_files = glob.glob(os.path.join(directory, "*.txt"))

    # 初始化计数器
    deleted_count = 0

    # 遍历每个 .txt 文件
    for txt_file in tqdm(txt_files):
        # 打开文件并读取内容
        with open(txt_file, "r", encoding="utf-8") as file:
            content = file.read()

        # 如果文件为空或仅包含空白字符，直接删除
        if not content.strip():
            os.remove(txt_file)
            deleted_count += 1
            continue

        # 将文件内容按段落分块
        paragraphs = content.split("\n")  # 假设段落以换行符分隔

        # 初始化标志变量
        file_matched = False

        # 遍历每个目标句子
        for sentence in target_sentences:
            # 如果文件已经匹配，跳过后续句子
            if file_matched:
                break

            # 遍历每个段落
            for paragraph in paragraphs:
                similarity = fuzz.partial_ratio(sentence, paragraph)
                if similarity >= similarity_threshold:
                    file_matched = True
                    break  # 找到匹配后跳出段落循环

        # 如果文件未匹配任何句子
        if not file_matched:
            deleted_count += 1
            os.remove(txt_file)  # 删除文件

    print(f"共删除 {deleted_count} 个文件。")


def main():
    # 第一步：从原始研报数据中提取 text 内容
    print("开始提取研报数据...")
    extract_text_from_reports(INPUT_DIRECTORY, OUTPUT_DIRECTORY)
    print("研报数据提取完成。")

    # 第二步：过滤研报数据，删除不包含目标句子的文件
    print("开始过滤研报数据...")
    filter_reports_by_sentences(OUTPUT_DIRECTORY, TARGET_SENTENCES, SIMILARITY_THRESHOLD)
    print("研报数据过滤完成。")


if __name__ == "__main__":
    main()
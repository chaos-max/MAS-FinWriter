from zhipuai import ZhipuAI
import os
import glob
from pathlib import Path
from tqdm import tqdm
client = ZhipuAI(api_key="") 

BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_DIR = Path(__file__).resolve().parent
input_directory = os.path.join(BASE_DIR, "data", "合并后的研报batch数据")
output_file = os.path.join(CURRENT_DIR, "batch_id.txt")
result_ids=[]
# # 获取所有 .jsonl 文件
jsonl_files = glob.glob(os.path.join(input_directory, "*.jsonl"))

for jsonl_file in tqdm(jsonl_files):
    result = client.files.create(
        file=open(jsonl_file, "rb"),
        purpose="batch"
    )
    result_ids.append(result.id)

for result_id in tqdm(result_ids):
    create = client.batches.create(
        input_file_id=result_id,
        endpoint="/v4/chat/completions", 
        auto_delete_input_file=True,
        metadata={
            "description": "classification"
        }
    )
    with open(output_file, 'a') as f:
        f.write(create.id + '\n')

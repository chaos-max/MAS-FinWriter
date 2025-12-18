from zhipuai import ZhipuAI
from tqdm import tqdm
import os
from pathlib import Path

client = ZhipuAI(api_key="") 

BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_DIR = Path(__file__).resolve().parent

output_directory = os.path.join(BASE_DIR, "data", "下载的batch数据")

os.makedirs(output_directory, exist_ok=True)

with open(os.path.join(CURRENT_DIR, "batch_id.txt"), "r") as f:
    lines = f.readlines()
    
    
for i, line in tqdm(enumerate(lines),total=len(lines)):
    batch_job = client.batches.retrieve(line.strip())
    output_id = batch_job.output_file_id
    content = client.files.content(output_id) 
    output_file_name = f"batchoutput_{i}.jsonl"
    output_file_path = os.path.join(output_directory, output_file_name)
    content.write_to_file(output_file_path)


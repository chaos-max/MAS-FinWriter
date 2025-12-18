import chinadata.ca_data as ts
import pandas as pd
import os
from datetime import datetime, timedelta
from tqdm import tqdm  # 确保是从 tqdm 导入 tqdm 函数

# 设置 Tushare 的 API Token
ts.set_token('ddd07f13a9e3344568fa716a88a289ecd95')
pro = ts.pro_api()
end_date = datetime.today()
start_date = datetime.strptime('20241220', '%Y%m%d')
date_range = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')  
# 用来存储所有板块的完整数据
all_data_dict = {}

# 确保输出目录存在
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '东方财富概念版块')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 使用 tqdm 进度条包裹循环
for date in tqdm(date_range, desc="Fetching data for each date", unit="day"):
    try:
        # 获取某个日期的概念板块数据
        df = pro.dc_index(trade_date=date, fields='name,trade_date,pct_change,total_mv,up_num,down_num')

        # 将数据按照 name 列分组并保存到字典中
        for name, group in df.groupby('name'):
            if name not in all_data_dict:
                all_data_dict[name] = group  # 如果字典中没有该概念板块，初始化
            else:
                all_data_dict[name] = pd.concat([all_data_dict[name], group], ignore_index=True)  # 如果已有该概念板块，合并数据
        
    except Exception as e:
        print(f"Error fetching data for {date}: {e}")

# 保存每个概念板块的数据到 CSV 文件
for name, data in all_data_dict.items():
    safe_name = name.replace('/', '_')  # 将 / 替换为 _
    file_name = os.path.join(output_dir, f"{safe_name}.csv")  # 根据板块名称创建文件名
    data.to_csv(file_name, index=False)  # 保存为 CSV 文件

print("Data fetching and saving complete.")

names_file_path = os.path.join(output_dir, "all_names.txt")
with open(names_file_path, "w", encoding="utf-8") as file:
    for name in all_data_dict.keys():
        safe_name = name.replace('/', '_')  # 将 / 替换为 _
        file.write(safe_name + ".csv" + "\n")  # 每个板块名称占一行

print(f"All names saved to {names_file_path}")
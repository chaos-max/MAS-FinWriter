import json
import os
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from gensim.models import KeyedVectors
from sklearn.cluster import DBSCAN
from tqdm import tqdm
import mmap

class IndustryAggregator:
    def __init__(self, w2v_path, mapping_file=None):
        # 加载词向量模型
        self.w2v = KeyedVectors.load(w2v_path)
        
        # 行业映射配置
        self.mapping_file = mapping_file or "industry_mapping.json"
        self.industry_mapping = {}
        self._load_mapping()
        
        # 预定义行业后缀
        self.suffix_pattern = re.compile(r'(行业|业|产业)$')
        
        # 聚类参数
        self.cluster_params = {
            'eps': 0.3,  # 聚类半径
            'min_samples': 2,  # 最小样本数
            'metric': 'cosine'  # 余弦相似度
        }

    def _load_mapping(self):
        """加载已有的行业映射"""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                self.industry_mapping = json.load(f)

    def _save_mapping(self):
        """保存行业映射"""
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.industry_mapping, f, ensure_ascii=False, indent=4)

    def is_contained_in(self, sub_name, full_name):
        """判断sub_name是否是full_name的前缀或后缀"""
        # 去除后缀（例如“行业”、“业”）
        sub_name = self.suffix_pattern.sub('', sub_name)
        full_name = self.suffix_pattern.sub('', full_name)
        
        # 判断sub_name是否为full_name的前缀或后缀
        return sub_name in full_name
    
    def optimize_standard_names(self):
        """确保每个标准名称是该组中最短的名称"""
        # 构建标准名称到原始名称列表的映射
        std_to_raws = defaultdict(list)
        for raw_name, std_name in self.industry_mapping.items():
            std_to_raws[std_name].append(raw_name)
        
        # 创建新映射字典
        new_mapping = {}
        updated = False
        
        for std_name, raw_names in std_to_raws.items():
            # 找到组内最短的名称（包括当前标准名称）
            all_names_in_group = raw_names + [std_name]
            # 去除“行业”和“业”后再比较长度
            stripped_names = [self.suffix_pattern.sub('', name) for name in all_names_in_group]
            shortest_name = min(stripped_names, key=lambda x: len(x.strip()))
            
            # 如果当前标准名称不是最短的，则使用最短的名称作为新的标准名称
            new_std_name = shortest_name if len(shortest_name.strip()) < len(std_name.strip()) else std_name
            
            # 如果标准名称有变化，标记需要更新
            if new_std_name != std_name:
                updated = True
            
            # 更新映射关系
            for raw_name in raw_names:
                new_mapping[raw_name] = new_std_name
        
        if updated:
            self.industry_mapping = new_mapping
        return updated
    
    def _get_word_vector(self, word):
        """安全获取词向量，处理未登录词"""
        # 先尝试直接获取
        if word in self.w2v:
            return self.w2v[word]
            
        # 尝试去除后缀后再查询
        base_word = self.suffix_pattern.sub('', word)
        if base_word in self.w2v:
            return self.w2v[base_word]
            
        # 字符级回退方案
        chars = [c for c in base_word if c in self.w2v]
        if chars:
            return np.mean([self.w2v[c] for c in chars], axis=0)
            
        # 最终回退到零向量
        return np.zeros(self.w2v.vector_size)

    def _cluster_industries(self, industry_names):
        """使用词向量聚类行业名称"""
        # 获取所有词向量
        vectors = [self._get_word_vector(name) for name in industry_names]
        
        # DBSCAN聚类
        clustering = DBSCAN(
            eps=self.cluster_params['eps'],
            min_samples=self.cluster_params['min_samples'],
            metric=self.cluster_params['metric']
        ).fit(vectors)
        
        # 构建聚类结果
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # 忽略噪声点
                clusters[label].append(industry_names[idx])
                
        return clusters

    def aggregate(self, industry_names):
        """两阶段聚合：规则匹配 + 语义聚类"""
        # 第一阶段：基于规则的精确匹配
        rule_based = defaultdict(list)
        for name in industry_names:
            base_name = self.suffix_pattern.sub('', name)
            rule_based[base_name].append(name)
        
        # 第二阶段：对剩余未匹配的进行语义聚类
        all_clustered = {}
        for base_name, variants in rule_based.items():
            if len(variants) == 1:  # 单个名称需要语义匹配
                clusters = self._cluster_industries([base_name] + list(self.industry_mapping.keys()))
                if clusters:
                    # 合并到最接近的已有类别
                    closest = next(iter(clusters.values()))[0]
                    all_clustered[base_name] = closest
                else:
                    # 作为新类别
                    all_clustered[base_name] = base_name
            else:
                # 多个变体使用基础名称作为标准
                all_clustered[base_name] = base_name
                
            # 更新映射关系
            for variant in variants:
                # 自动判断是否存在包含关系
                for existing_name in list(self.industry_mapping.keys()):
                    if self.is_contained_in(variant, existing_name):
                        self.industry_mapping[variant] = self.industry_mapping[existing_name]
                        break
                else:
                    # 如果没有找到包含关系，就维持原样
                    self.industry_mapping[variant] = base_name
                all_clustered[base_name] = self.industry_mapping[variant]
        
        return all_clustered



def extract_json_objects(file_path):
    """使用内存映射高效提取 JSON 对象（带进度条）"""
    with open(file_path, 'r+b') as f:
        file_size = f.seek(0, 2)
        f.seek(0)
        
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # 非贪婪匹配大括号包裹的 JSON 块（尽可能少）
            pattern = re.compile(rb'\{.*?\}(?=\s*\{|[\s\S]*$)', re.DOTALL)
            
            with tqdm(total=file_size, desc="🔍 正在解析 JSON", unit="B", unit_scale=True) as pbar:
                last_pos = 0
                for match in pattern.finditer(mm):
                    start, end = match.span()
                    chunk = match.group()
                    try:
                        obj = json.loads(chunk.decode('utf-8'))
                        yield obj
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass  # 忽略解析失败的块
                    finally:
                        pbar.update(end - last_pos)
                        last_pos = end
                        
                # 补全剩余进度
                pbar.update(file_size - last_pos)


def process_industry_data(input_file, output_dir, aggregator):
    """处理行业数据"""
    
    # 提取行业名称和因果关系
    industry_data = defaultdict(list)
    industry_names = set()
    for data in extract_json_objects(input_file):
        try:
            industry = data['industry']
            industry_names.add(industry)
            industry_data[industry].append(data['cause and effect'])
        except KeyError:
            continue
    
    # 执行聚合
    aggregator.aggregate(industry_names)
    
    # 优化标准名称
    aggregator.optimize_standard_names()
    
    # 生成输出文件
    Path(output_dir).mkdir(exist_ok=True)
    output_files = {}
    all_filenames = set()  # 新增：保存所有生成的文件名
    
    for raw_name, items in industry_data.items():
        std_name = aggregator.industry_mapping.get(raw_name, raw_name)
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', std_name)
        safe_name = safe_name + "业"  # 添加"业"后缀
        out_path = Path(output_dir) / f"{safe_name}.txt"
        
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(items) + "\n")
        
        output_files[std_name] = out_path
        all_filenames.add(safe_name)  # 记录文件名（不含后缀）

    
    # 保存所有文件名到txt文件（新增部分）
    filename_list_path = Path(output_dir) / "generated_files_list.txt"
    with open(filename_list_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(all_filenames))
    
    # 保存更新后的映射
    aggregator._save_mapping()
    return output_files

# 修改主程序部分
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    CURRENT_DIR = Path(__file__).resolve().parent
    # 初始化聚合器
    aggregator = IndustryAggregator(
        w2v_path=os.path.join(CURRENT_DIR, 'ChineseEmbedding.bin'),
        mapping_file=os.path.join(CURRENT_DIR, 'industry_mapping.json')
    )
    
    # 处理数据
    input_file = os.path.join(BASE_DIR, "data", "cause_and_effect.txt")
    output_dir = os.path.join(BASE_DIR, "data", "因果关系")
    
    result = process_industry_data(input_file, output_dir, aggregator)
    
    # 打印统计信息
    std_name_counts = defaultdict(list)
    for raw_name, std_name in aggregator.industry_mapping.items():
        std_name_counts[std_name].append(raw_name)
    
    print(f"生成 {len(result)} 个行业分类文件")
    print("所有生成的文件名已保存到: generated_files_list.txt")
    
    # 打印多对一映射关系
    multi_mapping_count = 0
    print("\n多对一映射关系:")
    for std_name, raw_names in sorted(std_name_counts.items(), key=lambda x: len(x[1]), reverse=True):
        if len(raw_names) > 1:
            multi_mapping_count += 1
            print(f"\n标准名称: {std_name} (包含 {len(raw_names)} 个变体)")
            for raw_name in raw_names:
                print(f"  - {raw_name}")
    
    print(f"\n总计发现 {multi_mapping_count} 个多对一映射组")
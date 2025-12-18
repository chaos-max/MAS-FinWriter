from metagpt.actions import Action
from pathlib import Path
import re
import numpy as np
from gensim.models import KeyedVectors
from metagpt.rag.engines import SimpleEngine
from llama_index.embeddings.zhipuai import ZhipuAIEmbedding
from metagpt.rag.schema import BM25RetrieverConfig
from finacial_writer.actions.Expert import Expert
import shutil
import os

embedding = ZhipuAIEmbedding(model="embedding-2", api_key="3114a609d68448efb5d459ee5b7e10da.3fbNyLNPdeOtoJbF")

class RagFix(Action):
    name: str = "FindFile"
    INDUSTRY_FILE_SEARCH_REQ: str = """
    从下面的列表中提取所有与{instruction}有关的行业。
    注意:
    1.返回的行业**必须包含**在给出的列表中。
    2.以 JSON 格式提供结果列表，如 [Word1、Word2、Word3]，不包括引号和其他字词。
    
    列表如下： 
    {content}
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 加载词向量模型
        model_path = Path(__file__).resolve().parents[2] / "研报处理/sgns.financial.gensim"
        self.w2v = KeyedVectors.load(str(model_path))
        self.suffix_pattern = re.compile(r'(行业|业)$')
    
    def _read_file(self, file_path: Path):
        with open(file_path, 'r') as f:
            industries = [line.strip() for line in f.readlines()]
            return industries
    def _read_input_file(self, file_path: Path):
        with open(file_path, 'r') as f:
            content = f.read()
            return content
        
    def _get_semantic_similar_industries(self, instruction: str, industries: list, top_n=20):
        """使用词向量找出语义相似的行业"""
        def get_vector(word):
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

        # 获取指令向量
        instr_vector = get_vector(instruction)
        if instr_vector is None:
            return industries  # 无法获取指令向量时返回全部

        # 计算每个行业的相似度
        industry_scores = []
        for industry in industries:
            industry_vec = get_vector(industry)
            if industry_vec is not None:
                similarity = np.dot(instr_vector, industry_vec)
                industry_scores.append((industry, similarity))
        
        # 按相似度排序并返回前top_n个
        industry_scores.sort(key=lambda x: x[1], reverse=True)
        return [industry for industry, _ in industry_scores[:top_n]]    

    def extract_and_add_prefix(self, text: str, prefix: str) -> list:
        # 正则表达式匹配文件名（假设文件名以 .csv 结尾）
        print(text)
        matches = re.findall(r'\[(.*?)\]', text,re.DOTALL)
        text = matches[0]
        text = [s.strip().strip('"') for s in text.split(",")]
        csv_files = [category + '.txt' for category in text]
        # 加上前缀路径
        full_paths = [f"{prefix}{file_name}" for file_name in csv_files]
        return full_paths
    
    
    def copy_files_to_new_folder(self, file_paths, target_folder):
        """
        将文件列表复制到新的目标文件夹
        
        参数:
            file_paths: 要复制的文件路径列表
            target_folder: 目标文件夹路径
            
        返回:
            成功复制的文件数量
        """
        # 确保目标文件夹存在
        target_path = Path(target_folder)
        target_path.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        
        for src_path in file_paths:
            try:
                src = Path(src_path)
                if src.is_file():
                    # 构建目标路径
                    dst = target_path / src.name
                    # 复制文件
                    shutil.copy2(src, dst)
                    copied_count += 1
                    print(f"已复制: {src.name}")
                else:
                    print(f"警告: 文件不存在 - {src_path}")
            except Exception as e:
                print(f"复制 {src_path} 时出错: {str(e)}")
        
        print(f"\n完成! 共成功复制 {copied_count}/{len(file_paths)} 个文件")
        return copied_count

    def read_summary_file(self, file_path: Path):
        # 示例Markdown内容（假设存储在变量md_content中）
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()

        # 正则表达式匹配每个块的url和summary
        pattern = re.compile(
            r'url: (https?://\S+)\s+summary: (.*?)(?=\n---|\Z)', 
            re.DOTALL  # 允许.匹配换行符
        )

        # 提取所有匹配项
        matches = pattern.findall(md_content)

        # 打印结果
        return matches
    async def run(self, instruction: str):
        instruction= self._read_input_file(self.config.project_path / 'docs' / 'input.txt')
        # instruction = "人工智能"  # 测试指令
        writer_root = Path(__file__).resolve().parents[2]
        name_path = writer_root / 'data/因果关系/generated_files_list.txt'
        all_industries = self._read_file(name_path)
        
        # 先进行语义筛选
        filtered_industries = self._get_semantic_similar_industries(
            instruction=instruction,
            industries=all_industries,
            top_n=20  # 筛选前20个最相关的
        )
        print(filtered_industries)
        prompt = self.INDUSTRY_FILE_SEARCH_REQ.format(instruction=instruction,content = filtered_industries)
        rsp = await self._aask(prompt)
        prefix = str(writer_root / "data/因果关系") + "/"
        # 提取文件名并加上前缀
        DATA_DIR = self.extract_and_add_prefix(rsp, prefix)
        target_folder = writer_root / "data/筛选结果"
    
        # 执行复制
        self.copy_files_to_new_folder(DATA_DIR, target_folder)
        store = SimpleEngine.from_docs(input_dir=target_folder,embed_model = embedding,retriever_configs=[BM25RetrieverConfig()])
        role = Expert(store=store)
        
        matches = self.read_summary_file(self.config.project_path / 'docs' / 'summaries.md')
        summaries = {}
        
        # Collect extracted logic to return
        extracted_logic_results = []

        # 临时禁用流式日志以避免大量 token 导致前端卡顿
        import metagpt.logs
        original_log_func = metagpt.logs._llm_stream_log
        
        # Check if we are in Chainlit environment
        is_chainlit = "chainlit" in getattr(original_log_func, "__name__", "").lower()
        
        if is_chainlit:
            metagpt.logs.set_llm_stream_logfunc(None)
        
        import asyncio
        from metagpt.logs import logger

        # 使用信号量限制并发数，防止过载
        sem = asyncio.Semaphore(3)

        async def process_summary(url, content, index, total):
            async with sem:
                query = f"""
                请从以下文本中提取与{instruction}有关的深层市场逻辑，要求：
                1. 提取短期和长期影响
                2. 提取深层逻辑
                文本：
                    {content}
                """
                logger.info(f"Processing summary {index + 1}/{total} for url: {url}")
                try:
                    rsp = await role.run(query)
                    return url, content + "\n" + rsp.content, rsp.content
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    return url, content, ""

        try:
            tasks = [process_summary(url, content, idx, len(matches)) for idx, (url, content) in enumerate(matches)]
            results = await asyncio.gather(*tasks)
            
            for url, processed_content, logic in results:
                summaries[url] = processed_content
                if logic:
                    extracted_logic_results.append(f"### Source: {url}\n{logic}")
        finally:
            # 恢复流式日志
            if is_chainlit and original_log_func:
                metagpt.logs.set_llm_stream_logfunc(original_log_func)

        with open(self.config.project_path / 'docs' / 'processed_summaries.md','w') as f:
            for url,content in summaries.items():
                f.write(f'url: {url}\n summary: \n{content}\n---\n')
        
        
        if os.path.exists(target_folder) and os.path.isdir(target_folder):
            shutil.rmtree(target_folder)
        
        # Return all extracted deep logic
        return "\n\n".join(extracted_logic_results) if extracted_logic_results else "未提取到相关深度逻辑。"
    

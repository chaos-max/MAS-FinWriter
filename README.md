# Financial Writer Agent

这是一个基于 MetaGPT 的金融行业研报生成智能体项目。它可以自动收集信息、分析数据、生成图表，并最终撰写详细的行业研究报告。

## 1. 环境搭建

### 创建 Conda 环境
```bash
conda create -n mas python=3.9.21
conda activate mas
```

### 安装依赖
```bash
# 安装项目依赖
pip install -r requirements.txt --no-deps

# 安装 MetaGPT (开发模式)
cd MetaGPT
pip install -e . --no-deps
pip install -e ".[rag]" --no-deps
cd ..
```

### 安装 Chainlit (用于可视化界面)
```bash
pip install chainlit
```

## 2. 数据准备

### 下载词向量模型
请下载以下词向量文件，并将其放置在 `writer/研报处理/` 目录下（例如：`writer/研报处理/sgns.financial.gensim`）。

*   **链接 1**: [百度网盘](https://pan.baidu.com/s/1Srki-SWrJt6-x-7nJGE-gg?pwd=wi3q) (提取码: wi3q)
*   **链接 2**: [百度网盘](https://pan.baidu.com/s/1E6rFwTce_baN9SPHZpu3lA?pwd=wi3q) (提取码: wi3q)

### 补充行业数据
请手动将您需要的行业数据文件添加至 `writer/data` 目录下。
现在已经有一些示例文件可供使用。

### 研报处理模块说明
`writer/研报处理` 模块用于预处理原始研报数据。

**工作流程**：
1. 内容提取
2. 章节分析
3. 章节提取
4. 转化batch
5. 合并batch文件
6. 上传batch
7. batch结果下载
8. batch结果处理
9. 合并结果

**作用**：
将非结构化研报数据转化为结构化格式，为后续分析提供数据支撑。

### 研报处理模块配置
该模块脚本位于 `writer/研报处理/` 目录下。运行前请注意：
1. **API Key 配置**：
   - 脚本 `研报第六次处理_上传batch.py` 和 `研报第七次处理_batch结果下载.py` 需要 ZhipuAI 的 API Key。
   - 脚本 `因果提取.py` 需要 OpenAI 兼容接口（如 DeepSeek）的 API Key。
   - 请在代码中填入您的 API Key。
2. **数据路径**：
   - 脚本默认使用相对路径，数据文件应存放在 `writer/data/` 目录下。
   - 原始研报数据请放入 `writer/data/原始研报数据/`。
3. **词向量模型**：
   - 请确保 `writer/研报处理/` 目录下存在 `ChineseEmbedding.bin`（需自己搜集下载） 和 `sgns.financial.bigram-char` 等词向量文件（视具体脚本需求而定）。

## 3. 配置

### 设置 API Key
请在配置文件 `MetaGPT/config/config2.yaml` 中填写您的 LLM (如 OpenAI, DeepSeek) 和 Search (如 SerpAPI, Google) 的 API Key 和相关配置。

### 添加新模型支持 (可选)
如果您使用了新的 LLM 模型，需要在 `MetaGPT/metagpt/utils/token_counter.py` 的第 230 行左右 (`TOKEN_MAX` 字典) 添加对应的 token 限制参数。

## 4. 运行项目

本项目支持命令行 (CLI) 和可视化界面 (UI) 两种运行方式。

### 方式一：命令行运行 (CLI)

直接运行 `main.py`。支持通过命令行参数自定义搜索深度。

```bash
# 默认运行 (默认 decomposition_nums=2, url_per_query=2)
python writer/main.py

# 自定义参数运行
# --idea: 研究主题
# --decomposition_nums: 生成查询关键词的数量
# --url_per_query: 每个查询抓取的 URL 数量
python writer/main.py --idea="人工智能" --decomposition_nums=3 --url_per_query=5
```

### 方式二：可视化界面运行 (Chainlit UI)

使用 Chainlit 启动 Web 界面，支持交互式对话和参数配置。

```bash
# 启动 Chainlit
chainlit run writer/UI_with_chainlit.py
```

启动后，在浏览器中打开显示的 URL。
1.  在对话框中输入研究主题（或点击示例）。
2.  系统会提示输入 `decomposition_nums` (查询数量) 和 `url_per_query` (URL数量)。
3.  智能体团队将开始工作，并在界面上实时展示进度和生成的报告/图表。

## 5. 常见问题与注意事项

*   **ChromeDriver 版本问题**: 项目已集成 `webdriver_manager`，会自动根据您的 Chrome 浏览器版本下载匹配的 ChromeDriver，无需手动配置。
*   **路径报错**: 如果遇到 `FileNotFoundError`，请确保您是在项目根目录下运行命令。项目已对大部分路径进行了绝对路径适配。
  

  
## 6. 输出结果

所有生成的研报、图表及中间文件将保存在 `writer/output` 目录下。
每次运行会根据研究主题生成一个新的文件夹。

目录结构示例：
- `docs/`: 包含生成的研报 (Markdown 格式)、需求文档和摘要。
- `image/`: 包含生成的分析图表 (PNG 格式)。
- `code/`: 包含执行的代码 Notebook 和计划文件。
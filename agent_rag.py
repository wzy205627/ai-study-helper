import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# --- 1. 配置 ---
# 请替换为你自己的 API Key
api_key = "sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl" 
base_url = "https://api.siliconflow.cn/v1"

print("🔄 正在初始化大脑...")

# --- 2. 准备左手：RAG 工具 (查 PDF) ---
# 这里我们先加载 PDF 并做好向量库，只做一次
# ⚠️ 确保你的文件夹里有 '课后题 (23版).pdf' 或者换成你自己的 PDF
pdf_path = "课后题（23版）.pdf" 

if os.path.exists(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    splits = splitter.split_documents(docs)
    
    # 初始化向量库
    # ✅ 修正后的写法（分批喂食）
    embeddings = OpenAIEmbeddings(
    api_key=api_key, 
    base_url=base_url, 
    model="BAAI/bge-m3",
    check_embedding_ctx_length=False,
    chunk_size=32  # 关键！每次只发 32 条，防止 API 报错
)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 定义工具函数：这不仅仅是代码，更是给 AI 看的“说明书”
    @tool
    def search_pdf_tool(query: str):
        """
        只有当用户询问关于'课后题'、'教材'、'文档内容'、'具体知识点'时，才使用这个工具。
        它会从本地的 PDF 文档中查找答案。
        """
        results = retriever.invoke(query)
        return "\n\n".join([doc.page_content for doc in results])
else:
    print(f"⚠️ 没找到 {pdf_path}，RAG 工具将不可用，请检查文件名。")
    # 定义一个空工具防止报错
    @tool
    def search_pdf_tool(query: str):
        """PDF 文件丢失，无法使用此工具"""
        return "没有找到文档。"

# --- 3. 准备右手：搜索工具 (查外网) ---
search_web_tool = DuckDuckGoSearchRun() 
# 给搜索工具加个描述，防止 AI 乱用（LangChain 默认其实有描述，但我们可以覆盖）
search_web_tool.name = "search_internet"
search_web_tool.description = "当用户询问实时新闻、当前发生的事件、或者 PDF 里肯定没有的外部知识时，使用这个工具。"

# --- 4. 组装 Agent ---
tools = [search_pdf_tool, search_web_tool]

llm = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model="deepseek-ai/DeepSeek-V3", # 用 V3 这种聪明的模型做决策更好
    temperature=0
)

# 定义 Prompt：告诉 AI 它是个全能助手
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手。你会根据问题自动判断：如果是书本知识就查 PDF，如果是外部新闻就查互联网。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"), # 这是 AI 思考和调用工具的“草稿纸”
])

# 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) # verbose=True 可以看到 AI 的思考过程

# --- 5. 测试时刻 ---
print("\n✅ 系统就绪！开始测试...\n")

# 测试 1：问 PDF 里的内容
query1 = "这门课的第一章讲了什么核心概念？"
print(f"🧑‍💻 用户问：{query1}")
agent_executor.invoke({"input": query1})

print("-" * 50)

# 测试 2：问外网的内容
query2 = "DeepSeek 这个公司是哪一年成立的？现在股价多少？"
print(f"🧑‍💻 用户问：{query2}")
agent_executor.invoke({"input": query2})
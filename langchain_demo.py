import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# --- 1. 配置 (还是用硅基流动) ---
# LangChain 会自动去读环境变量，也可以像下面这样显式传递
api_key = "sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl" # <--- ⚠️ 换成你的 Key
base_url = "https://api.siliconflow.cn/v1"

# 初始化模型 (LangChain 的包装器)
llm = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model="deepseek-ai/DeepSeek-V3",
    temperature=0.7
)

embeddings = OpenAIEmbeddings(
    api_key=api_key,
    base_url=base_url,
    model="BAAI/bge-m3",
    check_embedding_ctx_length=False,
    chunk_size=50 # <--- 关键！设置每次只发 50 个片段，避开 64 的限制
)

# --- 2. 加载与切分 (一气呵成) ---
print("📄 正在加载 PDF...")
# ⚠️ 这里请确保你目录下有一个 PDF 文件，比如 '课后题.pdf'
# 如果没有，请把之前用的 PDF 复制过来并改个简单的名字
loader = PyPDFLoader("课后题（23版）.pdf") 
docs = loader.load()

# 专业级切分器 (比我们之前按句号切分聪明多了)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

print(f"✅ 已切分为 {len(splits)} 个片段")

# --- 3. 向量库 (一键入库) ---
print("💾 正在存入向量库...")
# from_documents 会自动做 Embedding 并存入 Chroma
vectorstore = Chroma.from_documents(
    documents=splits, 
    embedding=embeddings
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # 找出前5名

# --- 4. 构建链 (The Chain) ---
# 这是 LangChain 最核心的概念：把“检索”和“生成”串起来

# 定义 Prompt 模板 (系统会自动把检索到的内容填入 {context})
prompt = ChatPromptTemplate.from_template("""
你是一个助手。请根据下面的上下文回答问题：
<context>
{context}
</context>

问题：{input}
""")

# 创建 "塞入文档链" (Stuff Documents Chain)
# 它的作用是：把检索到的 5 段话，“塞”进 Prompt 里发给 LLM
document_chain = create_stuff_documents_chain(llm, prompt)

# 创建 "检索链" (Retrieval Chain)
# 它的作用是：拿到用户问题 -> 去检索 -> 拿到结果 -> 扔给上面的 document_chain
rag_chain = create_retrieval_chain(retriever, document_chain)

# --- 5. 运行 ---
question = "这一章讲了什么核心概念？"
print(f"\n❓ 提问: {question}")

response = rag_chain.invoke({"input": question})

print("\n🤖 AI 回答:")
print(response["answer"])
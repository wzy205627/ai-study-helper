
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# ---------------------------------------------------------

import streamlit as st
import os
import tempfile
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# 页面配置
st.set_page_config(page_title="RAG 终极形态", page_icon="🧠")
st.title("🧠 你的私人知识库 (LangChain 版)")

# --- 2. 侧边栏：API Key 和 文件上传 ---
with st.sidebar:
    st.header("配置")
    api_key = st.text_input("SiliconFlow API Key", type="password", placeholder="sk-...")
    
    st.header("上传资料")
    uploaded_file = st.file_uploader("上传 PDF 文件", type=["pdf"])

# --- 3. 核心逻辑：处理文件并构建 RAG ---
if uploaded_file and api_key:
    # 3.1 临时保存上传的文件（因为 Loader 需要读取本地文件）
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # 3.2 加载与切分
    with st.spinner("正在阅读文档，请稍候..."):
        loader = PyPDFLoader(tmp_file_path)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        splits = text_splitter.split_documents(docs)
        
        # 3.3 向量化与存储 (关键：这里就是你之前没找到的那行代码)
        # 我们不指定 persist_directory，让它在内存中运行，这样云端最稳定
        embeddings = OpenAIEmbeddings(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1",
            model="BAAI/bge-m3",
            check_embedding_ctx_length=False,
            chunk_size=50 # 防止 413 报错
        )
        
        vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=embeddings
        )
        retriever = vectorstore.as_retriever()
        
        st.success(f"✅ 文档已处理，共切分为 {len(splits)} 个片段")

    # --- 4. 问答链 ---
    # 定义提示词模板
    prompt = ChatPromptTemplate.from_template("""
    你是一个智能助手。请根据下面的上下文回答用户的问题。
    如果上下文中没有答案，请诚实地说不知道。
    
    <context>
    {context}
    </context>

    问题：{input}
    """)
    
    # 初始化大模型
    llm = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1",
        model="deepseek-ai/DeepSeek-V3",
        temperature=0.7
    )
    
    # 构建链
    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    
    # --- 5. 聊天界面 ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 处理用户提问
    if user_input := st.chat_input("向文档提问..."):
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考..."):
                response = rag_chain.invoke({"input": user_input})
                answer = response["answer"]
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.info("👈 请先在左侧填入 API Key 并上传 PDF 文件")
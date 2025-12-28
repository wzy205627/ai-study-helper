# --- 1. 必须放在最开头的魔法补丁 (解决云端数据库报错) ---
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# -----------------------------------------------------

import streamlit as st
import os
import tempfile
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 页面配置
st.set_page_config(page_title="超级 AI 助手 (Agent版)", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ 超级 AI 助手 (能读 PDF + 能上网)")

# --- 2. 侧边栏配置 ---
with st.sidebar:
    st.header("配置中心")
    api_key = st.text_input("SiliconFlow API Key", type="password", placeholder="sk-...")
    st.info("💡 提示：上传 PDF 后，我会优先查文档；没文档或查不到时，我会自动上网搜！")
    uploaded_file = st.file_uploader("上传 PDF (可选)", type=["pdf"])

# --- 3. 初始化核心逻辑 ---
if api_key:
    # 定义大脑 (LLM)
    llm = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1",
        model="deepseek-ai/DeepSeek-V3", # V3 脑子好使，适合做决策
        temperature=0.1 # 降低创造性，让它更听话
    )

    # 准备工具列表
    tools = []

    # 3.1 准备右手：联网搜索工具 (永远可用)
    search_tool = DuckDuckGoSearchRun()
    search_tool.name = "search_internet"
    search_tool.description = "用于搜索互联网上的实时新闻、股票数据、或 PDF 里没有的通用知识。"
    tools.append(search_tool)

    # 3.2 准备左手：PDF 检索工具 (有文件才启用)
    if uploaded_file:
        with st.spinner("正在处理文档..."):
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # 加载与切分
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
            splits = splitter.split_documents(docs)

            # 向量化 (带防报错参数)
            embeddings = OpenAIEmbeddings(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1",
                model="BAAI/bge-m3",
                check_embedding_ctx_length=False,
                chunk_size=32
            )
            
            # 存入内存数据库
            vectorstore = Chroma.from_documents(splits, embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

            # 定义 PDF 工具函数
            @tool
            def search_pdf(query: str):
                """只有当用户询问关于上传的 PDF 文档内容、具体细节或书本知识时，必须使用这个工具。"""
                results = retriever.invoke(query)
                return "\n\n".join([doc.page_content for doc in results])
            
            tools.append(search_pdf)
            st.toast(f"✅ 文档已就绪！Agent 现有 {len(tools)} 个工具可用", icon="🤖")

    # --- 4. 组装 Agent ---
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个超级助手。你会根据问题自动判断：查文档(如果有)还是查互联网。请直接给出最终答案，不要啰嗦工具调用的细节。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # --- 5. 聊天界面 ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("问我任何事... (比如：DeepSeek股价多少？或者 PDF 里讲了什么？)"):
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            # 这是一个很酷的 UI 组件，能显示 AI 正在调用什么工具
            with st.status("🕵️‍♂️ AI 正在思考与搜索...", expanded=True) as status:
                try:
                    result = agent_executor.invoke({"input": user_input})
                    response = result["output"]
                    status.update(label="✅ 思考完成", state="complete", expanded=False) # 思考完自动折叠
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    status.update(label="❌ 发生错误", state="error")
                    st.error(f"Agent 出错了: {e}")

else:
    st.info("👈 请先在左侧输入 API Key 才能启动超级助手")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import sys
import json
import os
from openai import OpenAI

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 数据分析师", page_icon="📊", layout="wide")

# 解决中文乱码问题 (针对 Windows 系统的 SimHei 字体，Mac 用户可能需要换成 Arial Unicode MS)
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

st.title("📊 AI 数据分析师 (Agent 版)")

# --- 2. 初始化 Session State (记忆) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
你是一个 Python 数据分析专家。
用户会上传文件，文件路径固定为 'uploaded_data.csv' (如果是 Excel 则是 'uploaded_data.xlsx')。
请编写 Python 代码来分析数据。
⚠️ 关键绘图规则：
1. 如果需要画图，请务必使用 `plt.savefig('plot.png')` 将图片保存到本地，不要使用 plt.show()。
2. 画完图后，请在回复中明确告诉用户“图表已生成”。
"""}
    ]

# --- 3. 侧边栏：配置与上传 ---
with st.sidebar:
    st.header("1. 配置")
    # 这里的 Key 还是填你的
    api_key = st.text_input("SiliconFlow API Key", value="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl", type="password")
    
    st.header("2. 上传数据")
    uploaded_file = st.file_uploader("上传 CSV 或 Excel", type=["csv", "xlsx"])
    
    if uploaded_file:
        # 把上传的文件保存到本地固定路径，方便 Agent 读取
        file_ext = os.path.splitext(uploaded_file.name)[1]
        file_path = f"uploaded_data{file_ext}"
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"文件已就绪: {file_path}")
        
        # 简单预览一下数据
        if file_ext == ".csv":
            df_preview = pd.read_csv(file_path)
        else:
            df_preview = pd.read_excel(file_path)
        st.dataframe(df_preview.head(3))

# --- 4. 核心工具：代码执行器 (为了 Web 安全做了微调) ---
def execute_python(code):
    """在 Streamlit 中执行代码并捕获输出"""
    # 创建一个缓冲区来捕获 print 输出
    new_stdout = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = new_stdout
    
    try:
        # 为了让 AI 能画图，我们需要传入 plt
        # 为了让 AI 能接着分析上一轮的数据，我们需要传入全局变量 globals()
        exec(code, globals())
        output = new_stdout.getvalue()
        return json.dumps({"status": "success", "output": output})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
    finally:
        sys.stdout = old_stdout # 恢复标准输出

# 工具定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "执行 Python 代码进行数据分析或绘图。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"}
                },
                "required": ["code"]
            }
        }
    }
]

available_functions = {"execute_python": execute_python}

# --- 5. 聊天主界面 ---

# 显示历史消息 (跳过 System Prompt)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "tool_output": # 自定义一种类型用于显示图表
        if "plot.png" in msg["content"]:
            st.chat_message("assistant").image("plot.png")

# 处理用户输入
if prompt := st.chat_input("比如：统计各产品的销售总额并画图"):
    if not api_key:
        st.error("请先在侧边栏填写 API Key")
        st.stop()
        
    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    
    # 1. 显示用户问题
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Agent 思考与执行循环
    with st.chat_message("assistant"):
        # 创建一个状态容器，用来折叠显示复杂的代码执行过程
        status_container = st.status("🤖 AI 正在思考...", expanded=True)
        
        while True:
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[m for m in st.session_state.messages if m["role"] != "tool_output"], # 过滤掉图表消息以免干扰
                tools=tools
            )
            
            msg = response.choices[0].message
            
            # 如果 AI 想执行代码
            # 如果 AI 想执行代码
            if msg.tool_calls:
                # 🛠️ 关键修改：加 .model_dump() 把对象转成字典
                st.session_state.messages.append(msg.model_dump())
                
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    code = args.get("code")
                    
                    # 在状态容器里显示代码，让用户知道 AI 在写什么
                    status_container.write(f"🏃‍♂️ 正在执行代码...")
                    status_container.code(code, language="python")
                    
                    # 执行代码
                    result = execute_python(code)
                    
                    # 显示执行结果
                    result_json = json.loads(result)
                    if result_json["status"] == "success":
                        status_container.write(f"✅ 输出: {result_json['output']}")
                    else:
                        status_container.error(f"❌ 报错: {result_json.get('error')}")

                    # 将结果塞回给 AI
                    st.session_state.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": result
                    })
                    
                    # 🔍 关键检测：如果生成了图片，立马展示出来！
                    if os.path.exists("plot.png"):
                        # 检查这个 plot.png 是不是刚刚生成的（简单判断文件存在即可）
                        # 我们把图片展示逻辑放在循环外或者专门的消息类型里会更好，
                        # 但为了实时反馈，直接在这里显示
                        st.image("plot.png", caption="AI 生成的图表")
                        # 稍微改名防止下一轮重复读取（可选优化，这里暂不复杂化）
                        
            else:
                # AI 完成任务，输出最终回复
                final_reply = msg.content
                status_container.update(label="✅ 分析完成", state="complete", expanded=False)
                st.write(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})
                
                # 如果这一轮生成了图，我们也在历史记录里记一笔，确保刷新后还在
                if os.path.exists("plot.png"):
                     st.session_state.messages.append({"role": "tool_output", "content": "plot.png"})
                     
                break
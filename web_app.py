import streamlit as st
from openai import OpenAI
import random  # 导入随机库
import time    # 导入时间库
import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')


# --- 1. 页面配置 ---
st.set_page_config(page_title="神秘塔罗师", page_icon="🔮")
st.title("🔮 AI 塔罗牌占卜屋")

# --- 2. 准备塔罗牌数据 (这是我们的"牌库") ---
# 我们列出22张大阿卡纳牌
tarot_deck = [
    "红烧肉", "清蒸鱼", "拍黄瓜"
]

# --- 3. 配置 API (请务必填入你刚才测试成功的 Key 和 URL) ---
client = OpenAI(
    api_key="sk-b606a1f9579daa15887c5e5dfeee0dea",         # <--- 替换成你的 Key
    base_url="https://apis.iflow.cn/v1" # <--- 替换成你的 Base URL
)

# --- 4. 初始化聊天记录 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一位神秘的塔罗牌占卜大师。用户会提出问题，系统会告诉你用户抽到了哪张牌。请你根据用户的问题和这张牌的含义，给出富有哲理和神秘感的解读。"}
    ]

# --- 5. 显示之前的对话 ---
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 6. 核心逻辑区域 ---
if user_input := st.chat_input("心中默念你的问题（如：我最近的财运如何？）..."):
    
    # A. 显示用户的问题
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ================= 关键改动开始 =================
    
    # B. 增加“洗牌”动画 (st.spinner)
    with st.chat_message("assistant"):
        with st.spinner("🎴 正在洗牌中...命运之轮开始转动..."):
            time.sleep(2) # 让程序故意停顿2秒，制造仪式感
        
        # C. 真的随机抽一张牌 (Python 逻辑) 
        selected_card =random.choice(tarot_deck)
        
        # 显示抽到的牌
        st.write(f"✨ **命运指引你抽到了：【{selected_card}】**")
        
        # D. 构建这一轮的 Prompt (Prompt Engineering)
        # 我们要把“用户的问题”和“抽到的牌”拼在一起发给 AI
        # 这种写法叫 f-string (格式化字符串)
        full_prompt = f"用户想吃：'{user_input}'。既然没有，就向他推荐今天的特价菜：'{selected_card}'，并吹嘘一下这道菜多好吃。"

        # E. 发送给 AI
        stream = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3", # 记得确认模型名字
            messages=[
                # 这里有一个小技巧：我们不把 history 全发过去，
                # 而是只发系统设定 + 这一轮的完整指令，这样 AI 每一轮都是专注解牌
                {"role": "system", "content": "你是一位神秘的塔罗牌占卜大师。"},
                {"role": "user", "content": full_prompt}
            ],
            stream=True
        )
        
        # F. 显示 AI 的解读
        response = st.write_stream(stream)
    
    # ================= 关键改动结束 =================
    
    # 记录到历史 (虽然这里其实每轮都是新的，但为了保持格式，还是加上)
    st.session_state.messages.append({"role": "assistant", "content": response})
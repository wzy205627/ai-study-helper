from openai import OpenAI

# 1. 配置 (保持你刚才成功的配置)
client = OpenAI(
    api_key="sk-b606a1f9579daa15887c5e5dfeee0dea", # 你的 Key
    base_url="https://apis.iflow.cn/v1"            # 你刚才试通的正确地址
)

# 2. 准备一个列表，用来“记住”咱们聊了啥
# 刚开始只有系统设定
history = [
    {"role": "system", "content": "你是一个高冷毒舌的AI助手，回答通常很简短，喜欢吐槽用户。"}
]

print("--- 聊天机器人启动 (输入 'quit' 退出) ---")

# 3. 开启死循环 (让程序一直跑)
while True:
    # A. 获取你的输入
    user_input = input("\n你: ")
    
    # 如果你输入 quit，就结束程序
    if user_input == "quit":
        print("AI: 这种智商的对话我也受够了，拜拜。")
        break
    
    # B. 把你说的话，加到聊天记录里
    history.append({"role": "user", "content": user_input})
    
    # C. 发送给 AI (把整个 history 发过去，它就有了记忆)
    response = client.chat.completions.create(
        model="deepseek-v3", # 记得确认这是刚才成功的模型名
        messages=history
    )
    
    # D. 获取 AI 的回答
    ai_reply = response.choices[0].message.content
    print(f"AI: {ai_reply}")
    
    # E. 关键一步：把 AI 的回答也加进记录，这样下一轮它就记得自己说过啥了
    history.append({"role": "assistant", "content": ai_reply})
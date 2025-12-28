import json
from openai import OpenAI

# --- 1. 配置 (跟之前一样) ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 必填：你的硅基流动 Key
    base_url="https://api.siliconflow.cn/v1"
)

# --- 2. 定义工具 (这是我们的“手表”) ---
# 这是一个普通的 Python 函数，用来模拟查天气
def get_current_weather(location, unit="celsius"):
    """查询某个地点的天气 (模拟数据)"""
    print(f"🕵️‍♂️ 正在调用本地函数查询 {location} 的天气...")
    if "北京" in location:
        return json.dumps({"location": "北京", "temperature": "22", "unit": unit, "weather": "晴朗"})
    elif "上海" in location:
        return json.dumps({"location": "上海", "temperature": "18", "unit": unit, "weather": "多云"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

# --- 3. 告诉 AI 它有哪些工具可用 ---
# 这段 JSON 是写给 AI 看的“说明书”
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当用户询问天气时调用此函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

# --- 4. 测试：问它天气 ---
print("🤖 正在思考...")
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3", # 硅基流动的 DeepSeek 模型支持 Function Calling
    messages=[
        {"role": "user", "content": "今天北京的天气怎么样？"} 
    ],
    tools=tools_schema, # <--- 关键点：把工具箱递给它！
    tool_choice="auto", # 让 AI 自己决定要不要用工具
)

# --- 5. 看看 AI 返回了什么 ---
message = response.choices[0].message

print("\n📦 AI 的回复结构:")
print(message)

# 检查 AI 是否想用工具
if message.tool_calls:
    print("\n🎉 成功！AI 决定调用工具！")
    tool_name = message.tool_calls[0].function.name
    tool_args = message.tool_calls[0].function.arguments
    print(f"👉 它想调用的函数名: {tool_name}")
    print(f"👉 它提取的参数: {tool_args}")
else:
    print("\n🤷‍♂️ AI 决定只陪聊，不干活。")
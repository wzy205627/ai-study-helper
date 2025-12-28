import json
from openai import OpenAI
import math # <--- 新增
# --- 1. 配置 ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 别忘了填你的 Key
    base_url="https://api.siliconflow.cn/v1"
)
# --- 工具 1: 计算器 ---
def calculate(expression):
    """计算数学表达式"""
    try:
        # ⚠️ 警告: 实际生产中用 eval 很危险，但自己在本地玩玩没事
        result = eval(expression, {"__builtins__": None}, {"math": math})
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- 工具 2: 写文件助手 ---
def save_to_file(filename, content):
    """把内容写入本地文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"文件 {filename} 已保存！"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# 更新工具字典
available_functions = {
    "calculate": calculate,
    "save_to_file": save_to_file,
}
# # --- 2. 定义工具 (真正的干活函数) ---
# def get_current_weather(location, unit="celsius"):
#     """查询天气的函数"""
#     # 这里我们还是用假数据，实际开发中你可以换成 `requests.get("气象局API")`
#     if "北京" in location:
#         return json.dumps({"location": "北京", "temperature": "22", "unit": unit, "weather": "晴朗"})
#     elif "上海" in location:
#         return json.dumps({"location": "上海", "temperature": "18", "unit": unit, "weather": "多云"})
#     else:
#         return json.dumps({"location": location, "temperature": "unknown"})

# # 建立一个“工具字典”，方便代码根据名字找到函数
# available_functions = {
#     "get_current_weather": get_current_weather,
# }

# # --- 3. 对话开始 ---
# messages = [
#     {"role": "user", "content": "帮我查一下北京和上海的天气，然后告诉我哪里更适合穿短袖？"}
# ]

# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_current_weather",
#             "description": "查询天气",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "location": {"type": "string", "description": "城市名"},
#                     "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#                 },
#                 "required": ["location"],
#             },
#         },
#     }
# ]
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，支持 + - * / 和 math 函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 12 * 34"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_file",
            "description": "将文本保存到本地文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "文件名，如 result.txt"},
                    "content": {"type": "string", "description": "要保存的文本内容"},
                },
                "required": ["filename", "content"],
            },
        },
    }
]
messages = [
    {"role": "user", "content": "请帮我计算 3.14 乘以 123 的平方是多少？算出结果后，帮我写一个'math_report.txt'的文件，里面写上：'本次计算结果是：[结果] Verified by AI'。"}
]
print(f"👤 用户: {messages[0]['content']}")

# --- 4. 第一轮：AI 思考并决定调用工具 ---
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

response_message = response.choices[0].message
tool_calls = response_message.tool_calls

# --- 5. 关键步骤：如果有工具调用，我们就执行它 ---
if tool_calls:
    print(f"\n🤖 AI 决定调用 {len(tool_calls)} 次工具...")
    
    # A. 必须把 AI 的这个“决定”加入历史记录，否则 AI 会失忆
    messages.append(response_message)

    # B. 遍历所有工具调用 (可能一次查两个城市)
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # 找到对应的 Python 函数
        # function_to_call = available_functions[function_name]
        
        # print(f"   🏃‍♂️ 正在执行: {function_name} 参数: {function_args}")
        
        # # 真的运行函数！
        # function_response = function_to_call(
        #     location=function_args.get("location"),
        #     unit=function_args.get("unit"),
        # )
        # 找到对应的 Python 函数
        function_to_call = available_functions[function_name]
        
        print(f"   🏃‍♂️ 正在执行: {function_name} 参数: {function_args}")
        
        # ✨ 魔法时刻：使用 ** 自动解包参数
        # 意思是：不管 function_args 字典里有什么，都自动匹配给函数
        function_response = function_to_call(**function_args)
        print(f"   ✅ 函数返回: {function_response}")

        # C. 把函数的运行结果，包装成一条“tool”类型的消息，塞回给 AI
        messages.append(
            {
                "tool_call_id": tool_call.id, # 必须带上 ID，让 AI 知道这是哪个命令的结果
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
        )

    # --- 6. 第二轮：AI 拿到结果，生成最终回复 ---
    print("\n🤖 AI 正在根据结果生成最终回答...")
    second_response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=messages, # 这时候 messages 里包含了：用户问题 + AI指令 + 工具结果
    )
    
    print(f"\n🌟 AI 最终回复: \n{second_response.choices[0].message.content}")

else:
    print("AI 没调用工具，直接回了。")
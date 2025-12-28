import json
import math
from openai import OpenAI

# --- 1. 配置 ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 填你的 Key
    base_url="https://api.siliconflow.cn/v1"
)

# --- 2. 增强版工具 ---
def calculate(expression):
    """计算数学表达式"""
    try:
        # 🛡️ 自动修复：把 AI 习惯的数学符号 ^ 换成 Python 的 **
        expression = expression.replace("^", "**")
        result = eval(expression, {"__builtins__": None}, {"math": math})
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

def save_to_file(filename, content):
    """保存文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"文件 {filename} 已保存！"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

available_functions = {
    "calculate": calculate,
    "save_to_file": save_to_file,
}

# --- 3. 工具说明书 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_file",
            "description": "保存文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filename", "content"],
            },
        },
    }
]

# --- 4. 主程序：进入“自动驾驶”模式 ---
messages = [
    {"role": "user", "content": "请帮我计算 3.14 乘以 123 的平方是多少？算出结果后，帮我写一个'math_report.txt'的文件，里面写上：'本次计算结果是：[结果] Verified by AI'。"}
]

print(f"👤 用户: {messages[0]['content']}")

# 🔄 循环开始：只要 AI 想调工具，就一直转！
while True:
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=messages,
        tools=tools,
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 如果 AI 决定调工具...
    if tool_calls:
        print(f"\n🤖 AI 决定调用 {len(tool_calls)} 个工具...")
        messages.append(response_message) # 把“想调工具”这个念头记在小本本上

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"   🏃‍♂️ 执行: {function_name} 参数: {function_args}")
            
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args) # ⚡️ 魔法解包
            
            print(f"   ✅ 结果: {function_response}")

            # 把结果塞回给 AI
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        # ⚠️ 关键：循环继续！回到开头，让 AI 看看拿着结果还要不要做下一步
    else:
        # 如果 AI 不想调工具了，说明活干完了，输出最终回复并退出循环
        print(f"\n🌟 AI 最终回复: {response_message.content}")
        break
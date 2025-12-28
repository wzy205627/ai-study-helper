import pandas as pd
import random

# 模拟 100 条销售数据
data = {
    "日期": pd.date_range(start="2024-01-01", periods=100),
    "产品": [random.choice(["手机", "电脑", "耳机", "手表"]) for _ in range(100)],
    "价格": [random.choice([2000, 5000, 200, 1500]) for _ in range(100)],
    "数量": [random.randint(1, 5) for _ in range(100)],
}

df = pd.DataFrame(data)
df["总金额"] = df["价格"] * df["数量"]

# 保存为 Excel
filename = "sales_data.csv" # 用 CSV 比较通用
df.to_csv(filename, index=False, encoding='utf-8-sig')
print(f"✅ 模拟数据已生成：{filename}")

import json
import io
import sys
from openai import OpenAI
import pandas as pd # 预先导入，方便 AI 使用
import matplotlib.pyplot as plt

# --- 1. 配置 ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 换成你的 Key
    base_url="https://api.siliconflow.cn/v1"
)

# --- 2. 核心工具：代码执行器 ---
# 这是一个“沙盒”，允许 AI 的代码在这里跑
def execute_python(code):
    print(f"\n🐍 正在执行 AI 写的 Python 代码:\n{'-'*20}\n{code}\n{'-'*20}")
    
    # 捕获代码的 print 输出
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        # ⚠️ 高能预警：exec 是危险函数，它能执行任何 Python 代码
        # 在本地自己玩没问题，千万别直接放服务器上给外人因为
        # 这里的 globals() 让 AI 可以访问我们导入的 pd, plt 等库
        exec(code, globals()) 
        result = new_stdout.getvalue()
        if not result:
            result = "代码执行成功，但没有 print 输出。"
        return json.dumps({"output": result, "status": "success"})
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        sys.stdout = old_stdout # 恢复控制台输出

# 工具字典
available_functions = {
    "execute_python": execute_python,
}

# --- 3. 工具说明书 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "执行 Python 代码。用于数据分析、读取文件 (pandas)、绘图 (matplotlib) 或复杂计算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                },
                "required": ["code"],
            },
        },
    }
]

# --- 4. 主程序 ---
# 我们给它一个具体的分析任务
user_query = """
当前目录下有个 'sales_data.csv' 文件。
请帮我用 pandas 读取它，然后：
1. 统计每种产品的总销售额。
2. 画一个柱状图展示结果，并保存为 'result_chart.png'。
3. 告诉我哪个产品卖得最好。
"""

messages = [
    {"role": "system", "content": "你是一个 Python 数据分析专家。由于你看不到文件内容，你必须通过编写 Python 代码来读取文件 (df = pd.read_csv) 并打印相关信息 (print) 来进行分析。"},
    {"role": "user", "content": user_query}
]

print(f"👤 用户需求: {user_query}")

# 循环 (Agent Loop)
while True:
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=messages,
        tools=tools,
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        print(f"\n🤖 AI 决定写代码来分析...")
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # 执行 AI 写的代码
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)
            
            print(f"   ✅ 代码运行结果: {function_response[:200]}...") # 只打印前200个字防止刷屏

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
    else:
        print(f"\n🌟 AI 最终结论: \n{response_message.content}")
        break
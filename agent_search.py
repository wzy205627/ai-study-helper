import json
from openai import OpenAI
from duckduckgo_search import DDGS # 引入搜索引擎

# --- 1. 配置 ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 记得换成你的硅基流动 Key
    base_url="https://api.siliconflow.cn/v1"
)

# --- 2. 定义工具：联网搜索 ---
def search_web(query):
    """联网搜索工具"""
    print(f"🕵️‍♂️ 正在去互联网搜索：{query} ...")
    try:
        # 使用 DuckDuckGo 搜索，获取前 3 条结果
        results = DDGS().text(keywords=query, max_results=3)
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

# 定义工具字典
available_functions = {
    "search_web": search_web,
}

# --- 3. 工具说明书 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "当用户询问实时新闻、不知道的知识或当前事件时，调用此函数进行搜索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    }
]

# --- 4. 主程序 ---
# 这是一个经典的“DeepSeek V3”刚发布时的问题，老模型肯定不知道
question = "DeepSeek V3 是什么时候发布的？它有什么特点？请帮我搜一下并总结。"

messages = [
    {"role": "user", "content": question}
]

print(f"👤 用户: {question}")

while True:
    # 呼叫 AI
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=messages,
        tools=tools,
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        print(f"\n🤖 AI 决定联网搜索...")
        messages.append(response_message) 

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # 执行搜索
            function_to_call = available_functions[function_name]
            # 这里的 **function_args 会把 {"query": "..."} 拆开传进去
            search_result = function_to_call(**function_args)
            
            print(f"   ✅ 搜索结果已获取 (数据量: {len(search_result)} 字符)")

            # 把搜索到的网页摘要塞回给 AI
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": search_result,
                }
            )
    else:
        # AI 拿到搜索结果后，生成的最终回答
        print(f"\n🌟 AI 最终回复: \n{response_message.content}")
        break
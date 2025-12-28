# import numpy as np
# from openai import OpenAI
# import streamlit as st # 我们借用 streamlit 的 secrets 功能来拿 Key，或者你直接填也行

# # --- 1. 配置 API ---
# # ⚠️ 注意：Embedding 需要专门的模型！
# # 如果你用的是 DeepSeek 官方，模型名通常叫 "deepseek-embed"
# # 如果你用的是 硅基流动(SiliconFlow)，可能是 "BAAI/bge-m3" 或 "text-embedding-3-small" (看平台支持)
# # 如果你不知道用啥，先试着填 "text-embedding-3-small" (这是 OpenAI 标准名，很多中转商兼容)
# EMBEDDING_MODEL = "BAAI/bge-m3" 

# # 这里填你的配置，或者从 web_app.py 抄过来
# client = OpenAI(
#     api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",          # <--- 换成你的 Key
#     base_url="https://api.siliconflow.cn/v1"  # <--- 换成你的 Base URL
# )

# # --- 2. 定义一个函数：把文字变成数字 ---
# def get_embedding(text):
#     try:
#         # 这里的接口是 client.embeddings (不是 chat.completions)
#         response = client.embeddings.create(
#             input=text,
#             model=EMBEDDING_MODEL
#         )
#         # 拿到那一串长长的数字列表
#         return response.data[0].embedding
#     except Exception as e:
#         print(f"❌ 出错啦：{e}")
#         return None

# # --- 3. 定义余弦相似度公式 (Cosine Similarity) ---
# # 这是高中数学：计算两个向量夹角的余弦值。
# # 值越接近 1，说明两个向量方向越一致（越相似）。
# def cosine_similarity(v1, v2):
#     return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# # --- 4. 实验开始！---
# target_sentence = "我爱吃苹果"
# comparison_words = ["水果", "手机", "卡车", "喜欢", "讨厌"]

# print(f"🎯 目标句子：【{target_sentence}】\n")
# print("正在把文字变成数字向量... (可能需要几秒钟)")

# # 1. 先把目标句子变成向量
# v_target = get_embedding(target_sentence)

# if v_target:
#     # 2. 遍历对比词，看看谁的得分高
#     for word in comparison_words:
#         v_word = get_embedding(word)
#         if v_word:
#             score = cosine_similarity(v_target, v_word)
#             print(f" - 和【{word}】的相似度：{score:.4f}")
import chromadb
from chromadb.utils import embedding_functions

# --- 1. 初始化数据库 ---
# 我们创建一个只有内存的数据库（程序一关就清空），方便测试
print("📚 正在初始化 ChromaDB 数据库...")
chroma_client = chromadb.Client()

# 创建一个集合 (Collection)，你可以把它理解为一张“表”
# 名字随便起，比如叫 "my_knowledge_base"
collection = chroma_client.create_collection(name="demo_collection")

# --- 2. 准备入库的数据 ---
documents = [
    "苹果含有丰富的维生素C，有助于增强免疫力。",
    "乔布斯在2007年发布了第一代苹果手机。",
    "卡车司机通常需要在这个加油站休息。",
    "深度求索 (DeepSeek) 是中国最强的大模型之一。",
    "我喜欢吃香蕉和西瓜。"
]

# 给每条数据一个身份证号 (ID)
ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]

# --- 3. 存入数据库 (自动向量化！) ---
# ⚠️ ChromaDB 自带了一个简单的 Embedding 模型 (all-MiniLM-L6-v2)
# 它会自动下载并运行，你甚至不需要配 API Key！(虽然只支持英文比较好，但简单中文也能凑合)
print("📥 正在把数据存入数据库 (Chroma 会自动把它们变成向量)...")
collection.add(
    documents=documents,
    ids=ids
)

# --- 4. 模拟用户搜索 ---
user_query = "我想买个电子产品"

print(f"\n🔍 用户正在搜：【{user_query}】")
print("--------------------------------")

# 去数据库里搜，找最相似的 2 条
results = collection.query(
    query_texts=[user_query],
    n_results=2 
)

# --- 5. 显示结果 ---
# Chroma 会返回：
# 'documents': 搜到的原文
# 'distances': 距离（越小越相似，注意这里不是相似度，是距离）
for i in range(len(results['documents'][0])):
    doc = results['documents'][0][i]
    dist = results['distances'][0][i]
    print(f"✅ 找到结果 {i+1} (距离 {dist:.4f}):\n   👉 {doc}")
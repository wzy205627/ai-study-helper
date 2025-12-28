import chromadb
from openai import OpenAI
import numpy as np

# --- 1. 配置硅基流动 API (用来做 Embedding) ---
client = OpenAI(
    api_key="sk-xiewteiwyqvqsaxehcttthserqjbkzyywsmwgaignexanxvl",  # <--- ⚠️ 必填：换成你的硅基流动 Key
    base_url="https://api.siliconflow.cn/v1"
)

# 定义一个函数：专门找硅基流动要把向量
def get_silicon_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="BAAI/bge-m3" # 咱们验证过的最强免费中文模型
    )
    return response.data[0].embedding

# --- 2. 准备数据 ---
documents = [
    "苹果含有丰富的维生素C，有助于增强免疫力。",
    "乔布斯在2007年发布了第一代苹果手机。",  # <--- 这才是我们想要的
    "卡车司机通常需要在这个加油站休息。",
    "深度求索 (DeepSeek) 是中国最强的大模型之一。",
    "我喜欢吃香蕉和西瓜。"
]
ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]

# --- 3. 初始化数据库 ---
print("📚 初始化 ChromaDB...")
chroma_client = chromadb.Client()
# ⚠️ 注意：这里加了一个 metadata 参数，指定用 "cosine" 算法
# 既然名字改了，我们也换个新名字 "manual_rag_v2" 防止和旧数据打架
collection = chroma_client.create_collection(
    name="manual_rag_v2",
    metadata={"hnsw:space": "cosine"} 
)

# --- 4. 关键步骤：手动把字变成向量，再存进去 ---
print("⚡️ 正在调用硅基流动 API 生成向量 (可能需要几秒)...")

# 我们创建一个空列表，用来装所有句子的向量
doc_embeddings = []

for doc in documents:
    print(f"   -> 处理：{doc[:10]}...")
    vector = get_silicon_embedding(doc) # 调用 API
    doc_embeddings.append(vector)

# 把 原文 + 向量 一起存进去
# 注意：这次我们加了 embeddings 参数！Chroma 就不用自己那个笨模型了
collection.add(
    documents=documents,
    embeddings=doc_embeddings, # <--- 注入灵魂！
    ids=ids
)

# --- 5. 搜索时刻 ---
query = "苹果手机"
print(f"\n🔍 用户搜：【{query}】")

# 把用户的搜索词也变成向量
query_vector = get_silicon_embedding(query)

# 用向量去搜向量
results = collection.query(
    query_embeddings=[query_vector], # <--- 用我们算好的向量去搜
    n_results=5
)

# --- 6. 揭晓答案 ---
print("\n🎉 搜索结果：")
for i in range(len(results['documents'][0])):
    doc = results['documents'][0][i]
    dist = results['distances'][0][i] # 这里是距离，越小越好
    print(f"   👉 {doc} (距离: {dist:.4f})")
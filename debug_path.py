import sys
import os

print(f"🐍 Python 解释器位置: {sys.executable}")
print(f"📂 当前工作目录: {os.getcwd()}")

print("-" * 30)

try:
    import langchain
    print(f"✅ 成功导入 langchain！")
    print(f"📍 它竟然是从这里加载的: {langchain.__file__}")
    
    if "site-packages" in str(langchain.__file__):
        print("🎉 恭喜！这是正版包（在 site-packages 里）。")
    else:
        print("🚨 抓到了！这是冒牌货！它不在 site-packages 里！")
        print("👉 请立刻把这个文件或文件夹改名！")

except ImportError:
    print("❌ 依然无法导入 langchain。")
except Exception as e:
    print(f"❓ 发生了其他错误: {e}")
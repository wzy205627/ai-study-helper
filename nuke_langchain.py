import os
import sys
import shutil

# 1. 找到 site-packages 的准确位置
site_packages = next(p for p in sys.path if 'site-packages' in p)
print(f"📍 定位到 site-packages: {site_packages}")

# 2. 定义我们要“追杀”的目标
# 目标 A: 那个冒牌的 langchain.py 文件
target_file = os.path.join(site_packages, "langchain.py")
# 目标 B: 那个可能坏掉的 langchain 文件夹
target_dir = os.path.join(site_packages, "langchain")
# 目标 C: 安装信息文件夹 (metadata)
dist_info_pattern = "langchain-"

print("-" * 30)

# --- 执行清除任务 A: 删除冒牌文件 ---
if os.path.exists(target_file):
    try:
        os.remove(target_file)
        print(f"✅ 成功删除冒牌文件: {target_file}")
    except Exception as e:
        print(f"❌ 删除文件失败: {e}")
else:
    print("💨 没有发现冒牌文件 langchain.py (很好！)")

# --- 执行清除任务 B: 删除主文件夹 ---
if os.path.exists(target_dir):
    try:
        shutil.rmtree(target_dir)
        print(f"✅ 成功删除损坏的文件夹: {target_dir}")
    except Exception as e:
        print(f"❌ 删除文件夹失败: {e}")
else:
    print("💨 没有发现 langchain 文件夹")

# --- 执行清除任务 C: 删除安装信息 (让 pip 以为没装过) ---
count = 0
for item in os.listdir(site_packages):
    if item.startswith("langchain-") and item.endswith(".dist-info"):
        full_path = os.path.join(site_packages, item)
        try:
            shutil.rmtree(full_path)
            count += 1
            print(f"   🗑️ 已清理残留信息: {item}")
        except:
            pass
if count > 0:
    print(f"✅ 清理了 {count} 个残留安装记录")

print("-" * 30)
print("🎉 清理完毕！现在环境是干净的了。")
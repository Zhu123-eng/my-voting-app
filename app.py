import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import hashlib

# --- 配置与常量 ---
DATA_FILE = "votes.json"
DEFAULT_OPTIONS = [
    "鲜铺", 
    "东北菜馆", 
    "环球渔市", 
    "川菜馆", 
    "80年代", 
    "外婆小院", 
    "长弄堂", 
    "小湘诸",
    "313羊庄",
    "徐小厨农家菜",
    "药膳鸡火锅",
]

# --- 数据处理 ---
def load_data():
    default_data = {
        "options": {opt: 0 for opt in DEFAULT_OPTIONS}, 
        "voters_ids": [],    # 存储设备指纹
        "voters_names": []   # 存储投票人姓名
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 兼容旧版本数据
            if "voters_ids" not in data:
                data["voters_ids"] = data.get("voters", [])
            if "voters_names" not in data:
                data["voters_names"] = []
            return data
    except Exception:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 获取设备唯一指纹 (不依赖 Session) ---
def get_device_fingerprint():
    try:
        # 1. 尝试从 Header 获取 IP (特别是经过内网穿透时)
        forwarded_for = st.context.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0]
        else:
            # 备选：尝试直接获取远程地址 (如果可用)
            ip = getattr(st.context, "remote_ip", "unknown_ip")
        
        # 2. 获取浏览器特征 (User-Agent)
        ua = st.context.headers.get("User-Agent", "unknown_ua")
        
        # 3. 组合成唯一哈希
        fingerprint = f"{ip}-{ua}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
    except Exception:
        # 如果获取失败，返回一个通用标识，让程序继续运行
        return "generic_device_id"

device_id = get_device_fingerprint()

# --- 初始化数据 ---
data = load_data()

# --- 页面设置 ---
st.set_page_config(page_title="团建投票小程序", page_icon="🗳️", layout="centered")

# 自定义 CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #07c160;
        color: white;
    }
    .voted-msg {
        padding: 20px;
        background-color: #e8f5e9;
        color: #2e7d32;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🗳️ 团建投票小程序")

# --- 检查当前设备是否已投票 ---
has_voted_device = device_id in data["voters_ids"]

if not has_voted_device:
    st.subheader("请填写信息并投票")
    
    # 1. 姓名输入
    user_name = st.text_input("请输入你的真实姓名（必填）：").strip()
    
    # 2. 选项选择
    option_selected = st.radio("请选择心仪的餐厅：", list(data["options"].keys()), label_visibility="collapsed")

    if st.button("提交投票"):
        if not user_name:
            st.error("请输入姓名后再提交！")
        elif user_name in data["voters_names"]:
            st.warning(f"姓名 '{user_name}' 已经投过票了，请勿重复投票。")
        else:
            # 再次从文件读取以确保数据同步
            data = load_data()
            if device_id not in data["voters_ids"] and user_name not in data["voters_names"]:
                data["options"][option_selected] += 1
                data["voters_ids"].append(device_id)
                data["voters_names"].append(user_name)
                save_data(data)
                st.success(f"投票成功！感谢 {user_name} 参与。")
                st.balloons()
                st.rerun()
            else:
                st.warning("检测到已投票记录。")
else:
    st.markdown('<div class="voted-msg">✅ 你的设备已完成投票，感谢参与！</div>', unsafe_allow_html=True)

# --- 结果展示 ---
st.divider()
st.subheader("📊 实时投票结果")

df = pd.DataFrame(list(data["options"].items()), columns=["选项", "票数"])

if df["票数"].sum() > 0:
    fig = px.bar(df, x="选项", y="票数", text="票数", color="选项",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示已投票名单（可选，增加透明度）
    with st.expander("查看已投票名单"):
        st.write(", ".join(data["voters_names"]) if data["voters_names"] else "暂无")
else:
    st.info("目前还没有投票，快来抢占第一票吧！")

# --- 管理功能 ---
with st.expander("⚙️ 管理设置"):
    admin_key = st.text_input("请输入管理密钥以重置投票：", type="password")
    if st.button("清空所有投票记录"):
        if admin_key == "123":
            data = {
                "options": {opt: 0 for opt in DEFAULT_OPTIONS}, 
                "voters_ids": [], 
                "voters_names": []
            }
            save_data(data)
            st.warning("数据已重置！")
            st.rerun()
        else:
            st.error("密钥错误。")

# --- 页脚 ---
st.caption("基于设备指纹与姓名双重校验 | 数据自动持久化保存")

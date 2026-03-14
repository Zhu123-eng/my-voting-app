import streamlit as st
import json
import os
import hashlib
import pandas as pd
import altair as alt
from datetime import datetime

# 文件路径配置
VOTES_FILE = 'votes.json'

def load_votes():
    """加载投票数据"""
    if os.path.exists(VOTES_FILE):
        try:
            with open(VOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_votes(votes):
    """保存投票数据"""
    with open(VOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(votes, f, ensure_ascii=False, indent=4)

def reset_votes():
    """重置投票数据"""
    if os.path.exists(VOTES_FILE):
        os.remove(VOTES_FILE)
    st.rerun()

def get_user_fingerprint():
    """生成用户指纹"""
    remote_ip = getattr(st.context, "remote_ip", "unknown_ip")
    headers = getattr(st.context, "headers", {})
    if "x-forwarded-for" in headers:
        remote_ip = headers["x-forwarded-for"].split(",")[0]
    user_agent = headers.get("user-agent", "unknown_ua")
    fingerprint_raw = f"{remote_ip}-{user_agent}"
    return hashlib.md5(fingerprint_raw.encode()).hexdigest()

def main():
    # 设置页面
    st.set_page_config(page_title="团建投票小程序", page_icon="🗳️", layout="centered")
    
    # 自定义样式：让界面更接近截图
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #00c853;
            color: white;
            border-radius: 20px;
            padding: 0.5rem 2rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #00a844;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # 标题
    st.markdown("<h1 style='text-align: center;'>📸 团建投票小程序</h1>", unsafe_allow_html=True)

    # 加载数据
    votes_data = load_votes()
    fingerprint = get_user_fingerprint()
    
    voted_fingerprints = [v['fingerprint'] for v in votes_data]
    voted_names = [v['name'] for v in votes_data]
    
    # 选项列表
    all_options = [
        "鲜铺",
        "东北饺子馆",
        "环球渔市",
        "川菜馆",
        "80年代",
        "外婆小院",
        "长弄堂",
        "小湘诸",
        "313羊庄",
        "徐小厨农家菜",
        "药膳鸡火锅",
        "毛家大院",
        "海鲜宫",
        "大诸暨"
    ]

    # 判断是否投过票
    has_voted = fingerprint in voted_fingerprints

    if has_voted:
        # 截图1样式：已投票提示
        st.success("✅ 你的设备已完成投票，感谢参与！")
    else:
        # 截图2样式：投票表单
        st.subheader("请填写信息并投票")
        st.caption("请输入你的真实姓名（必填）：")
        name = st.text_input("姓名输入框", label_visibility="collapsed", placeholder="")
        
        option = st.radio(
            "选项列表",
            all_options,
            label_visibility="collapsed"
        )
        
        if st.button("提交投票"):
            if not name.strip():
                st.error("请输入姓名后再提交！")
            elif name.strip() in voted_names:
                st.error("该姓名已被使用，请换一个。")
            else:
                new_vote = {
                    "name": name.strip(),
                    "option": option,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "fingerprint": fingerprint
                }
                votes_data.append(new_vote)
                save_votes(votes_data)
                st.rerun()

    st.markdown("---")

    # 实时投票结果
    st.subheader("📊 实时投票结果")
    
    if votes_data:
        # 构造绘图数据
        counts = {opt: 0 for opt in all_options}
        for v in votes_data:
            opt_name = v['option']
            if opt_name in counts:
                counts[opt_name] += 1
            else:
                # 兼容旧数据或未知选项
                counts[opt_name] = 1
        
        df = pd.DataFrame(list(counts.items()), columns=['选项', '票数'])
        
        # 使用 Altair 绘制更接近截图样式的柱状图（黄色柱子）
        chart = alt.Chart(df).mark_bar(color='#fbc02d').encode(
            x=alt.X('选项:N', sort=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('票数:Q', axis=alt.Axis(tickMinStep=1)),
            tooltip=['选项', '票数']
        ).properties(height=400)
        
        # 在柱子上添加数字标签
        text = chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5
        ).encode(
            text='票数:Q'
        )
        
        st.altair_chart(chart + text, use_container_width=True)
    else:
        st.info("目前还没有投票，快来抢占第一票吧！")

    # 查看已投票名单
    with st.expander("👁️ 查看已投票名单"):
        if votes_data:
            for v in votes_data:
                st.write(f"· {v['name']}")
        else:
            st.write("暂无名单")

    # 管理设置
    with st.expander("⚙️ 管理设置"):
        st.caption("请输入管理密钥以重置投票：")
        pwd = st.text_input("密钥输入", type="password", label_visibility="collapsed")
        if st.button("清空所有投票记录"):
            if pwd == "123":
                reset_votes()
            else:
                st.error("密钥错误！")

    # 页脚
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.8rem;'>基于设备指纹与姓名双重校验 | 数据自动持久化保存</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import json
import warnings
import os
import re
import numpy as np
import base64
import time
from google import genai
from google.genai import types

# 忽略无关警告
warnings.filterwarnings('ignore')

# ================= 1. 基础配置 =================

st.set_page_config(
    page_title="ChatBI Pro", 
    layout="wide", 
    page_icon="🧬", 
    initial_sidebar_state="expanded"
)

# --- 模型配置 ---
MODEL_FAST = "gemini-1.5-flash"           
MODEL_SMART = "gemini-1.5-pro"            

# --- 常量定义 ---
JOIN_KEY = "药品编码"
LOGO_FILE = "logo.png"

# --- 本地文件名定义 ---
FILE_FACT = "fact.xlsx"  
FILE_DIM = "ipmdata.xlsx"    

try:
    FIXED_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    FIXED_API_KEY = ""

# ================= 2. 视觉体系 (VI) =================

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --pc-primary-blue: #005ADE;
            --pc-dark-blue: #004099;
            --pc-bg-light: #F4F6F9;
            --pc-text-main: #1A2B47;
            --pc-text-sub: #5E6D82;
        }

        .stApp { background-color: var(--pc-bg-light); font-family: 'Inter', "Microsoft YaHei", sans-serif; color: var(--pc-text-main); }

        header[data-testid="stHeader"] {
            background-color: transparent !important;
            pointer-events: none !important; 
            z-index: 1000010 !important;
        }

        header[data-testid="stHeader"] button {
            pointer-events: auto !important;
            color: var(--pc-text-sub) !important;
        }

        [data-testid="stSidebarCollapsedControl"] {
            display: block !important;
            position: fixed !important;
            top: 18px !important;       
            left: 20px !important;
            z-index: 1000011 !important;
            background-color: white !important;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            color: var(--pc-primary-blue) !important;
            border: 1px solid #E6EBF5;
            display: flex !important;
            align-items: center;
            justify-content: center;
        }

        .fixed-header-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 64px;
            background-color: #FFFFFF;
            box-shadow: 0 2px 12px rgba(0, 90, 222, 0.08);
            z-index: 999999; 
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; border-bottom: 1px solid #E6EBF5;
            padding-left: 70px;
        }

        .summary-box {
            background-color: #FFFFFF; padding: 20px; border-radius: 8px;
            border: 1px solid #E6EBF5; border-left: 4px solid var(--pc-primary-blue); margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .summary-title { font-weight: 700; color: var(--pc-text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-size: 14px; }
        .summary-list li { margin-bottom: 6px; color: var(--pc-text-main); font-size: 13px; line-height: 1.5; }
        .summary-label { font-weight: 600; color: var(--pc-text-sub); margin-right: 8px; background: #F4F6F9; padding: 2px 6px; border-radius: 4px; font-size: 11px; }

        .mini-insight {
            background-color: #F8FAFC; padding: 12px 16px; border-radius: 6px;
            font-size: 13px; color: var(--pc-text-main); margin-top: 10px; margin-bottom: 20px;
            border: 1px solid #E6EBF5; border-left: 3px solid #FF9800;
        }
        .step-header {
            font-weight: 700; color: var(--pc-text-main); font-size: 16px; margin-top: 30px; 
            margin-bottom: 15px; display: flex; align-items: center;
        }
        .step-header::before {
            content: ''; display: inline-block; width: 4px; height: 18px;
            background: var(--pc-primary-blue); margin-right: 12px; border-radius: 2px;
        }
        </style>
    """, unsafe_allow_html=True)

# ================= 3. 工具函数 =================

@st.cache_resource
def get_client():
    if not FIXED_API_KEY: return None
    try: return genai.Client(api_key=FIXED_API_KEY, http_options={'api_version': 'v1beta'})
    except Exception as e: st.error(f"SDK Error: {e}"); return None

@st.cache_data
def load_local_data(filename):
    if not os.path.exists(filename): return None
    try:
        if filename.endswith('.csv'): df = pd.read_csv(filename)
        else: df = pd.read_excel(filename)
        df.columns = df.columns.str.strip()
        if JOIN_KEY in df.columns:
            df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        for col in df.columns:
            if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty']):
                try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                except: pass
            if any(k in str(col).lower() for k in ['日期', 'date', 'time', '月份']):
                try: df[col] = pd.to_datetime(df[col])
                except: pass
        return df
    except Exception as e: st.error(f"加载 {filename} 失败: {e}"); return None

def get_dataframe_info(df, name="df"):
    if df is None: return f"{name}: 未加载"
    info = [f"### 表名: `{name}` ({len(df)} 行)"]
    info.append("| 列名 | 类型 | 示例值 |")
    info.append("|---|---|---|")
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = str(list(df[col].dropna().unique()[:5]))
        info.append(f"| {col} | {dtype} | {sample} |")
    return "\n".join(info)

def clean_json_string(text):
    try: return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(0))
            except: pass
    return None

def normalize_result(res):
    if res is None: return pd.DataFrame()
    if isinstance(res, pd.DataFrame): return res
    if isinstance(res, pd.Series): return res.to_frame(name='数值').reset_index()
    if isinstance(res, dict):
        try: return pd.DataFrame([res]) 
        except:
            try: return pd.DataFrame(list(res.items()), columns=['指标', '数值'])
            except: pass
    return pd.DataFrame([str(res)], columns=['Result'])

def format_display_df(df):
    if not isinstance(df, pd.DataFrame): return df
    df_fmt = df.copy()
    for col in df_fmt.columns:
        if pd.api.types.is_numeric_dtype(df_fmt[col]):
            if any(x in str(col) for x in ['率', '比', 'Ratio']):
                df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "-")
            else:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "-")
    return df_fmt

def get_history_context(limit=5):
    """提取历史对话上下文"""
    history_msgs = st.session_state.get("messages", [])[:-1] 
    relevant_msgs = history_msgs[-(limit * 2):]
    context_str = ""
    if not relevant_msgs: return "无历史对话"
    for msg in relevant_msgs:
        role = "用户" if msg["role"] == "user" else "AI助手"
        content = msg["content"]
        if msg["type"] == "df": content = "[已展示数据表]"
        context_str += f"{role}: {content}\n"
    return context_str

def render_protocol_card(summary):
    """通用摘要卡片渲染"""
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">⚡ 执行协议</div>
        <ul class="summary-list">
            <li><span class="summary-label">意图</span> {summary.get('intent', '-')}</li>
            <li><span class="summary-label">范围</span> {summary.get('scope', '-')}</li>
            <li><span class="summary-label">指标</span> {summary.get('metrics', '-')}</li>
            <li><span class="summary-label">加工逻辑</span> {summary.get('logic', '-')}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ================= 4. 页面渲染 =================

inject_custom_css()
client = get_client()

if "messages" not in st.session_state: 
    st.session_state.messages = []

df_sales = load_local_data(FILE_FACT)
df_product = load_local_data(FILE_DIM)

with st.sidebar:
    st.markdown("### 📊 数据概览")
    if df_sales is not None:
        st.success(f"已加载: {FILE_FACT}")
        date_cols = df_sales.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        if len(date_cols) > 0:
            st.info(f"**数据时间范围**:\n\n{df_sales[date_cols[0]].min().date()} 至 {df_sales[date_cols[0]].max().date()}")
        st.dataframe(pd.DataFrame(df_sales.columns, columns=["Fact字段"]), height=150, hide_index=True)
    if df_product is not None:
        st.success(f"已加载: {FILE_DIM}")
        st.dataframe(pd.DataFrame(df_product.columns, columns=["Dim字段"]), height=150, hide_index=True)
    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Header ---
st.markdown("""<div class="fixed-header-container"><div class="nav-left"><span class="nav-title">ChatBI Pro</span></div></div>""", unsafe_allow_html=True)

# --- 渲染历史 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text": st.markdown(msg["content"])
        elif msg["type"] == "df": st.dataframe(msg["content"], use_container_width=True)

# --- 输入 ---
query = st.chat_input("🔎 请输入问题...")
if query:
    st.session_state.messages.append({"role": "user", "type": "text", "content": query})
    with st.chat_message("user"): st.markdown(query)

# --- 核心逻辑 ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    history_str = get_history_context(limit=5)
    
    with st.chat_message("assistant"):
        if df_sales is None or df_product is None: 
            st.error("无法读取本地数据文件。"); st.stop()
        
        context_info = f"{get_dataframe_info(df_sales, 'df_sales')}\n{get_dataframe_info(df_product, 'df_product')}\n关联键: {JOIN_KEY}"

        # 1. 意图分类
        with st.status("🔄 识别分析意图...", expanded=False) as status:
            prompt_router = f"历史:\n{history_str}\n当前问题: {user_query}\n分类: simple(查数)/analysis(深度)/irrelevant. 输出JSON: {{'type': '...'}}"
            resp = client.models.generate_content(model=MODEL_FAST, contents=prompt_router, config=types.GenerateContentConfig(response_mime_type="application/json"))
            intent = clean_json_string(resp.text).get('type', 'simple')
            status.update(label=f"意图: {intent.upper()}", state="complete")

        shared_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np}

        # 2. 模式执行
        if intent == 'simple':
            with st.spinner("⚡ 正在提取数据..."):
                prompt_code = f"历史:\n{history_str}\n问题: {user_query}\n数据信息:\n{context_info}\n输出JSON: {{'summary': {{'intent': '...', 'scope': '...', 'metrics': '...', 'logic': '...'}}, 'code': '...'}}"
                resp_code = client.models.generate_content(model=MODEL_SMART, contents=prompt_code, config=types.GenerateContentConfig(response_mime_type="application/json"))
                plan = clean_json_string(resp_code.text)
                if plan:
                    render_protocol_card(plan['summary'])
                    try:
                        exec(plan['code'], shared_ctx)
                        res_df = normalize_result(shared_ctx.get('result'))
                        st.dataframe(format_display_df(res_df), use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "type": "df", "content": format_display_df(res_df)})
                    except Exception as e: st.error(f"执行失败: {e}")

        elif intent == 'analysis':
            with st.spinner("🧠 深度分析拆解中..."):
                prompt_plan = f"历史:\n{history_str}\n问题: {user_query}\n数据信息:\n{context_info}\n拆解分析角度。输出JSON: {{'intent_analysis': '...', 'angles': [{{'title': '...', 'desc': '...', 'summary': {{'intent': '...', 'scope': '...', 'metrics': '...', 'logic': '...'}}, 'code': '...'}}]}}"
                resp_plan = client.models.generate_content(model=MODEL_SMART, contents=prompt_plan, config=types.GenerateContentConfig(response_mime_type="application/json"))
                plan_json = clean_json_string(resp_plan.text)
            
            if plan_json:
                st.markdown(f"### 意图深度解析\n{plan_json.get('intent_analysis')}")
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": plan_json.get('intent_analysis')})
                
                angles_summary = []
                for angle in plan_json.get('angles', []):
                    st.markdown(f"**角度: {angle['title']}**\n{angle['desc']}")
                    render_protocol_card(angle.get('summary', {}))
                    try:
                        exec(angle['code'], shared_ctx)
                        res_df = normalize_result(shared_ctx.get('result'))
                        if not res_df.empty:
                            st.dataframe(format_display_df(res_df), use_container_width=True)
                            st.session_state.messages.append({"role": "assistant", "type": "df", "content": format_display_df(res_df)})
                            # 洞察
                            mini_resp = client.models.generate_content(model=MODEL_FAST, contents=f"简要解读数据(50字内): {res_df.to_string()}")
                            st.markdown(f'<div class="mini-insight">💡 {mini_resp.text}</div>', unsafe_allow_html=True)
                            angles_summary.append(f"[{angle['title']}]: {mini_resp.text}")
                    except Exception as e: st.error(f"角度执行报错: {e}")

                if angles_summary:
                    final_resp = client.models.generate_content(model=MODEL_SMART, contents=f"基于发现总结问题: {user_query}\n发现: {angles_summary}\n陈述事实。")
                    st.markdown(f"### 综合业务洞察\n{final_resp.text}")
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": final_resp.text})

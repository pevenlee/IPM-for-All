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
MODEL_FAST = "gemini-2.0-flash-exp"       # 路由 & 简单洞察 & 追问生成
MODEL_SMART = "gemini-3-pro-preview"      # 写代码 & 深度分析

# --- 常量定义 ---
JOIN_KEY = "药品编码"
LOGO_FILE = "logo.png"

# --- 本地文件名定义 ---
FILE_FACT = "fact.xlsx"      # 销售事实表
FILE_DIM = "ipmdata.xlsx"    # 产品维度表

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
            display: flex !important;
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
            align-items: center;
            justify-content: center;
        }
        
        [data-testid="stSidebarCollapsedControl"]:hover {
            background-color: #F0F7FF !important;
            color: var(--pc-dark-blue) !important;
            transform: scale(1.05);
            transition: all 0.2s;
        }

        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }

        .fixed-header-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 64px;
            background-color: #FFFFFF;
            box-shadow: 0 2px 12px rgba(0, 90, 222, 0.08);
            z-index: 999999; 
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; border-bottom: 1px solid #E6EBF5;
            padding-left: 70px;
        }
        
        .nav-left { display: flex; align-items: center; }
        .nav-logo-img { height: 32px; width: auto; margin-right: 12px; }
        .nav-title { font-size: 18px; font-weight: 700; color: var(--pc-primary-blue); letter-spacing: 0.5px; }
        
        .nav-center { display: flex; gap: 32px; font-weight: 600; font-size: 15px; }
        .nav-item { color: var(--pc-text-sub); cursor: pointer; padding: 20px 4px; position: relative; }
        .nav-item.active { color: var(--pc-primary-blue); }
        .nav-item.active::after {
            content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px;
            background-color: var(--pc-primary-blue); border-radius: 2px 2px 0 0;
        }
        
        .nav-right { display: flex; align-items: center; gap: 16px; }
        .nav-avatar {
            width: 32px; height: 32px; background-color: var(--pc-primary-blue); color: white;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: bold; border: 2px solid #E6EBF5;
        }
        .nav-exit-btn {
            border: 1px solid #DCDFE6; padding: 5px 12px; border-radius: 4px;
            font-size: 13px; color: var(--pc-text-sub); background: white; cursor: pointer;
        }

        .block-container { padding-top: 80px !important; padding-bottom: 3rem !important; max-width: 1200px; }
        footer { display: none !important; }

        div.stButton > button { border: 1px solid #E6EBF5; color: var(--pc-text-main); background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
        div.stButton > button:hover { border-color: var(--pc-primary-blue); color: var(--pc-primary-blue); background-color: #F0F7FF; }
        
        .summary-box {
            background-color: #FFFFFF; padding: 20px; border-radius: 8px;
            border: 1px solid #E6EBF5; border-left: 4px solid var(--pc-primary-blue); margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .summary-title { font-weight: 700; color: var(--pc-text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-size: 14px; }
        .summary-list li { margin-bottom: 6px; color: var(--pc-text-main); font-size: 13px; line-height: 1.5; }
        .summary-label { font-weight: 600; color: var(--pc-text-sub); margin-right: 8px; background: #F4F6F9; padding: 2px 6px; border-radius: 4px; font-size: 11px; }

        .tech-card {
            background-color: white; padding: 24px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 20px;
            border: 1px solid #E6EBF5; transition: all 0.2s ease-in-out;
        }
        .tech-card:hover { transform: translateY(-2px); border-color: #B3C0D1; box-shadow: 0 8px 16px rgba(0,0,0,0.04); }
        .angle-title { font-size: 16px; font-weight: 700; color: var(--pc-primary-blue); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .angle-desc { font-size: 13px; color: var(--pc-text-sub); line-height: 1.5; margin-bottom: 16px; }

        .mini-insight {
            background-color: #F8FAFC; padding: 12px 16px; border-radius: 6px;
            font-size: 13px; color: var(--pc-text-main); margin-top: 10px; margin-bottom: 20px;
            border: 1px solid #E6EBF5; border-left: 3px solid #FF9800;
        }
        .insight-box {
            background: white; padding: 24px; border-radius: 12px; position: relative;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02); border: 1px solid #E6EBF5;
        }
        .insight-box::before {
            content: ''; position: absolute; left: 0; top: 12px; bottom: 12px;
            width: 4px; background: linear-gradient(180deg, var(--pc-primary-blue) 0%, #00C853 100%);
            border-radius: 0 4px 4px 0;
        }
        .step-header {
            font-weight: 700; color: var(--pc-text-main); font-size: 16px; margin-top: 30px; 
            margin-bottom: 15px; display: flex; align-items: center;
        }
        .step-header::before {
            content: ''; display: inline-block; width: 4px; height: 18px;
            background: var(--pc-primary-blue); margin-right: 12px; border-radius: 2px;
        }
        .error-box { 
            background: #FEF0F0; padding: 12px; border-radius: 6px; 
            color: #F56C6C; border: 1px solid #FDE2E2; font-size: 13px; display: flex; align-items: center; gap: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

# ================= 3. 核心工具函数 =================

@st.cache_resource
def get_client():
    if not FIXED_API_KEY: return None
    try: return genai.Client(api_key=FIXED_API_KEY, http_options={'api_version': 'v1beta'})
    except Exception as e: st.error(f"SDK Error: {e}"); return None

# --- [增强版] 数据读取与预处理 ---
@st.cache_data
def load_local_data(filename):
    if not os.path.exists(filename): return None
    df = None
    
    # 策略 1: 尝试作为标准 Excel 读取
    try:
        df = pd.read_excel(filename, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_csv(filename)
        except Exception:
            try:
                df = pd.read_csv(filename, encoding='gbk')
            except Exception:
                try:
                    df = pd.read_excel(filename, engine='xlrd')
                except Exception as e:
                    st.error(f"文件 {filename} 读取失败。错误: {e}")
                    return None

    if df is not None:
        # 1. 清洗列名
        df.columns = df.columns.str.strip()
        
        # 2. 关联键处理
        if JOIN_KEY in df.columns:
            df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
        for col in df.columns:
            # object 转 string
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)

            # 数值列清洗 (去逗号)
            if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty']):
                try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                except: pass
            
            # 日期/时间处理
            if any(k in str(col).lower() for k in ['日期', 'date', 'time', '月份', 'year', 'month', 'quarter', 'period', '年', '月', '季']):
                try: 
                    # 先尝试转为 datetime
                    df[col] = pd.to_datetime(df[col], errors='coerce').fillna(df[col])
                    
                    # [年季处理] 如果是时间类型且列名包含 '季'/'quarter'，强制转为 2024Q1 字符串
                    if df[col].dtype.kind == 'M' and any(x in str(col).lower() for x in ['季', 'quarter']):
                         df[col] = df[col].dt.to_period('Q').astype(str)
                except: 
                    pass
        return df
    return None

def get_dataframe_info(df, name="df"):
    if df is None: return f"{name}: 未加载"
    info = [f"### 表名: `{name}` ({len(df)} 行)"]
    info.append("| 列名 | 类型 | 示例值 (Top 5) |")
    info.append("|---|---|---|")
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = list(df[col].dropna().unique()[:5])
        info.append(f"| {col} | {dtype} | {str(sample)} |")
    return "\n".join(info)

def clean_json_string(text):
    try: return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(0))
            except: pass
    return None

def safe_generate(client, model, prompt, mime_type="text/plain"):
    config = types.GenerateContentConfig(response_mime_type=mime_type)
    try: 
        return client.models.generate_content(model=model, contents=prompt, config=config)
    except Exception as e: 
        return type('obj', (object,), {'text': f"Error: {e}"})

# --- [增强版] 智能格式化展示函数 ---
def format_display_df(df):
    """
    智能格式化 DataFrame 用于前端展示：
    1. 年季 (2024Q1)
    2. 年份 (2024, 无千分位)
    3. 比率/均值/单价 (1位小数)
    4. 常规金额/销量 (整数 + 千分位)
    """
    if not isinstance(df, pd.DataFrame): return df
    df_fmt = df.copy()
    
    for col in df_fmt.columns:
        col_str = str(col).lower()
        
        # 1. 尝试转换为数值，以便判断类型
        is_numeric = pd.api.types.is_numeric_dtype(df_fmt[col])
        
        # 如果是 object 但看起来像数字，尝试转一下（除了特定的ID列）
        if not is_numeric and df_fmt[col].dtype == 'object' and 'id' not in col_str and '编码' not in col_str:
            try:
                temp = pd.to_numeric(df_fmt[col], errors='coerce')
                if temp.notnull().sum() > 0:
                    is_numeric = True
            except: pass

        if is_numeric:
            # A. 年份处理 (Year, 年) -> 不加千分位，无小数
            if col_str in ['year', '年份', '年']:
                try:
                    df_fmt[col] = df_fmt[col].fillna(0).astype(int).astype(str).replace('0', '-')
                except: pass
                
            # B. 1位小数: 百分比/比率/均值/价格/份额 (除法结果通常属于此类)
            elif any(x in col_str for x in ['率', '比', 'ratio', 'share', '同比', '环比', '%', '价', 'price', 'avg', '均', 'average', '贡献', '份额']):
                # 如果数据已经是 0.25 这种小数
                if df_fmt[col].mean() < 1.1 and df_fmt[col].max() < 10: 
                     df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "-")
                # 如果数据已经是 25 这种整数 或 价格/均值
                else:
                     # 这里的逻辑涵盖了: 价格、均值、以及已经是整数百分比的列
                     df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:,.1f}" if pd.notnull(x) else "-")
                     # 如果明确是百分比列但值较大，可能需要手动加 %，这里为了通用性暂只保留1位小数
                     if any(k in col_str for k in ['率', '比', 'ratio', '%', 'share', '份额']):
                         df_fmt[col] = df_fmt[col].apply(lambda x: x + "%" if x != "-" and "%" not in x else x)

            # C. 常规金额/销量 (Sales, Qty, 额, 量) -> 0位小数 + 千分位
            else:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "-")
        
        # 非数值类型的特殊处理
        else:
            # D. 年季/日期处理
            # 检查是否为 datetime 类型
            if pd.api.types.is_datetime64_any_dtype(df_fmt[col]):
                if any(x in col_str for x in ['季', 'quarter']):
                     df_fmt[col] = df_fmt[col].dt.to_period('Q').astype(str) # 变成 2024Q1
                else:
                     df_fmt[col] = df_fmt[col].dt.strftime('%Y-%m-%d')
            
            # 如果已经是字符串，检查是否类似 "2024-01-01" 且列名含季
            elif df_fmt[col].dtype == 'object' and any(x in col_str for x in ['季', 'quarter']):
                 try:
                     temp_date = pd.to_datetime(df_fmt[col], errors='coerce')
                     mask = temp_date.notnull()
                     df_fmt.loc[mask, col] = temp_date[mask].dt.to_period('Q').astype(str)
                 except: pass

    return df_fmt

def normalize_result(res):
    if res is None: return pd.DataFrame()
    if isinstance(res, pd.DataFrame): return res
    if isinstance(res, pd.Series): return res.to_frame(name='数值').reset_index()
    if isinstance(res, dict):
        try: return pd.DataFrame([res]) 
        except:
            try: return pd.DataFrame(list(res.items()), columns=['指标', '数值'])
            except: pass
    if isinstance(res, list):
        try: return pd.DataFrame(res)
        except: return pd.DataFrame(res, columns=['结果'])
    return pd.DataFrame([str(res)], columns=['Result'])

def safe_check_empty(df):
    if df is None: return True
    if isinstance(df, pd.DataFrame): return df.empty
    try: return normalize_result(df).empty
    except: return True

def get_history_context(limit=5):
    history_msgs = st.session_state.messages[:-1] 
    relevant_msgs = history_msgs[-(limit * 2):]
    context_str = ""
    if not relevant_msgs: return "无历史对话"
    for msg in relevant_msgs:
        role = "用户" if msg["role"] == "user" else "AI助手"
        content = msg["content"]
        if msg["type"] == "df": 
            try:
                df_preview = msg["content"]
                cols = list(df_preview.columns)
                content = f"[已展示数据表: {len(df_preview)}行, 列: {cols}]"
            except:
                content = "[已展示数据表]"
        context_str += f"{role}: {content}\n"
    return context_str

def render_protocol_card(summary):
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">⚡ 执行协议</div>
        <ul class="summary-list">
            <li><span class="summary-label">意图</span> {summary.get('intent', '-')}</li>
            <li><span class="summary-label">范围</span> {summary.get('scope', '-')}</li>
            <li><span class="summary-label">关键匹配</span> {summary.get('key_match', '未涉及特定实体')}</li>
            <li><span class="summary-label">指标</span> {summary.get('metrics', '-')}</li>
            <li><span class="summary-label">加工逻辑</span> {summary.get('logic', '-')}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# [关键修复] 回调函数，专门用于处理动态按钮点击，防止rerun时丢失状态
def handle_followup(question):
    st.session_state.messages.append({"role": "user", "type": "text", "content": question})

# ================= 4. 页面渲染 =================

inject_custom_css()
client = get_client()

df_sales = load_local_data(FILE_FACT)
df_product = load_local_data(FILE_DIM)

# --- Header ---
logo_b64 = base64.b64encode(open(LOGO_FILE, "rb").read()).decode() if os.path.exists(LOGO_FILE) else ""
logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="nav-logo-img">' if logo_b64 else ""

st.markdown(f"""
<div class="fixed-header-container">
    <div class="nav-left">
        {logo_img}
        <span class="nav-title">ChatBI Pro</span>
    </div>
    <div class="nav-center">
        <div class="nav-item">HCM</div> 
        <div class="nav-item active">ChatBI</div>
        <div class="nav-item">Insight</div>
    </div>
    <div class="nav-right">
        <div class="nav-avatar">PRO</div>
        <button class="nav-exit-btn" onclick="alert('安全退出')">退出</button>
    </div>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📊 数据概览")
    if df_sales is not None:
        st.success(f"已加载: {FILE_FACT}")
        date_cols = df_sales.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        if len(date_cols) > 0:
            target_col = date_cols[0]
            try:
                min_date = df_sales[target_col].min().strftime('%Y-%m-%d')
                max_date = df_sales[target_col].max().strftime('%Y-%m-%d')
                st.info(f"**时间范围 ({target_col})**:\n\n{min_date} 至 {max_date}")
            except:
                st.info(f"**时间字段 ({target_col})** 已识别")
        else:
            st.caption("未检测到标准日期格式字段 (可能为季度/字符型)")
        st.divider()
        st.markdown("**包含字段:**")
        st.dataframe(pd.DataFrame(df_sales.columns, columns=["Fact字段"]), height=150, hide_index=True)
    else:
        st.error(f"未找到 {FILE_FACT}")

    if df_product is not None:
        st.success(f"已加载: {FILE_DIM}")
        st.dataframe(pd.DataFrame(df_product.columns, columns=["Dim字段"]), height=150, hide_index=True)
    else:
        st.error(f"未找到 {FILE_DIM}")

    st.divider()
    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text": st.markdown(msg["content"])
        elif msg["type"] == "df": st.dataframe(msg["content"], use_container_width=True)

# --- 猜你想问 ---
if not st.session_state.messages:
    st.markdown("### 💡 猜你想问")
    c1, c2, c3 = st.columns(3)
    def handle_preset(question):
        st.session_state.messages.append({"role": "user", "type": "text", "content": question})
        st.rerun()
    if c1.button("🗺️ 肿瘤产品的市场表现如何?"): handle_preset("肿瘤产品的市场表现如何?")
    if c2.button("💊 查一下K药最近的销售额"): handle_preset("查一下K药最近的销售额")
    if c3.button("📊 销售额过亿的，独家创新药有哪些"): handle_preset("销售额过亿的，独家创新药有哪些")

# --- Input ---
query = st.chat_input("🔎 请输入问题...")
if query:
    st.session_state.messages.append({"role": "user", "type": "text", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

# --- Core Logic ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    history_str = get_history_context(limit=5)

    with st.chat_message("assistant"):
        if df_sales is None or df_product is None:
            st.error(f"请确保根目录下存在 {FILE_FACT} 和 {FILE_DIM}")
            st.stop()

        context_info = f"""
        {get_dataframe_info(df_sales, "df_sales")}
        {get_dataframe_info(df_product, "df_product")}
        关联键: `{JOIN_KEY}`
        
        【重要业务知识库】
        1. 涉及“内资/外资”时，请使用 `df_product['企业类型']` 字段。
        
        【时间计算强制规则】
        1. **同比完整性校验**：在计算同比（Year-over-Year）时，必须检查基准期数据是否完整。
           - 场景：如果数据起始于 2023Q4（即2023年只有1个季度数据），而2024年有全年数据。禁止计算 "2024全年 vs 2023全年" 的同比。应自动调整为 "2024Q4 vs 2023Q4" 或仅展示最新完整周期。
        2. **市场规模默认口径**：当用户询问“市场规模”且未明确指定时间范围（如“2023年”、“上季度”）时：
           - 默认行为：必须使用**最新滚动年 (MAT)** 也就是数据中最新的连续4个季度之和。
        """

        # 1. 意图识别
        with st.status("🔄 思考中...", expanded=False) as status:
            prompt_router = f"""
            你是一个精准的意图分类专家。请基于用户问题和历史对话判断意图。
            
            【历史对话】
            {history_str}
            
            【当前用户问题】
            "{user_query}"
            
            【分类标准】
            1. simple (简单取数): 
               - 包含明确的“提取”、“查询”、“列出”、“多少”、“数据”等关键词。
               - 用户基于上一轮结果进行简单筛选（如“只看华东的”）。
               
            2. analysis (深度分析): 
               - 询问“为什么”、“原因”、“趋势”、“表现如何”、“评价”。
               - 需要多维度拆解、归因分析。
               
            3. irrelevant (无关): 非业务数据问题。
            
            输出 JSON: {{ "type": "simple/analysis/irrelevant" }}
            """
            resp = safe_generate(client, MODEL_FAST, prompt_router, "application/json")
            if "Error" in resp.text:
                status.update(label="API 错误", state="error")
                st.error(f"API 调用失败: {resp.text}")
                st.stop()
            intent = clean_json_string(resp.text).get('type', 'simple')
            status.update(label=f"意图: {intent.upper()}", state="complete")

        shared_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np}

        # 2. 简单查询
        if intent == 'simple':
            with st.spinner(f"⚡ 正在生成代码 ({MODEL_SMART})..."):
                prompt_code = f"""
                你是一位医药行业的 Python 专家。
                
                【历史对话】(用于理解指代)
                {history_str}
                
                【当前用户问题】
                "{user_query}"
                
                【数据上下文】 {context_info}
                
                【指令】 
                1. 严格按用户要求提取字段。
                2. 使用 `pd.merge` 关联两表 (除非用户只查单表)。
                3. **重要**: 确保所有使用的变量（如 market_share）都在代码中明确定义。不要使用未定义的变量。
                4. **绝对禁止**导入 IPython 或使用 display() 函数。
                5. 禁止使用 df.columns = [...] 强行改名，请使用 df.rename()。
                6. **避免 'ambiguous' 错误**：如果 index name 与 column name 冲突，请在 reset_index() 前先使用 `df.index.name = None` 或重命名索引。
                7. 结果存为 `result`。
                
                【摘要生成规则 (Summary)】
                - scope (范围): 数据的筛选范围，时间范围。
                - metrics (指标): 用户查询的核心指标。
                - key_match (关键匹配): **必须说明**提取了用户什么词，去匹配了哪个列。例如："提取用户词 'K药' -> 模糊匹配 '商品名' 列"。
                - logic (加工逻辑): 简述筛选和计算步骤，严禁提及“表关联”、“Merge”等技术术语。
                
                输出 JSON: {{ "summary": {{ "intent": "简单取数", "scope": "...", "metrics": "...", "key_match": "...", "logic": "..." }}, "code": "..." }}
                """
                resp_code = safe_generate(client, MODEL_SMART, prompt_code, "application/json")
                plan = clean_json_string(resp_code.text)
            
            if plan:
                s = plan.get('summary', {})
                render_protocol_card(s)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"**执行协议**: {s.get('intent', '-')}"})

                if 'result' in shared_ctx: del shared_ctx['result']
                
                try:
                    exec(plan['code'], shared_ctx)
                    res_raw = shared_ctx.get('result')
                    res_df = normalize_result(res_raw)
                    
                    if not safe_check_empty(res_df):
                        formatted_df = format_display_df(res_df)
                        st.dataframe(formatted_df, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "type": "df", "content": formatted_df})
                    else:
                        st.warning("⚠️ 结果为空，尝试模糊搜索...")
                        fallback_code = f"result = df_product[df_product.astype(str).apply(lambda x: x.str.contains('{user_query[:2]}', case=False, na=False)).any(axis=1)].head(10)"
                        try:
                            exec(fallback_code, shared_ctx)
                            res_fallback = normalize_result(shared_ctx.get('result'))
                            if not safe_check_empty(res_fallback):
                                st.dataframe(res_fallback)
                                st.session_state.messages.append({"role": "assistant", "type": "df", "content": res_fallback})
                            else:
                                msg = "在产品库中也未找到相关信息。"
                                st.error(msg)
                                st.session_state.messages.append({"role": "assistant", "type": "text", "content": msg})
                        except:
                            st.error("查询无结果。")
                except Exception as e:
                    st.error(f"代码错误: {e}")

        # 3. 深度分析
        elif intent == 'analysis':
            # [关键修复] 使用 copy() 防止数据在分析过程中被意外修改污染全局缓存
            shared_ctx = {
                "df_sales": df_sales.copy(), 
                "df_product": df_product.copy(), 
                "pd": pd, 
                "np": np
            }

            with st.spinner(f"🧠 专家拆解分析思路 ({MODEL_SMART})..."):
                prompt_plan = f"""
                你是一位医药行业高级分析师。
                
                【历史对话】
                {history_str}
                
                【当前用户问题】
                "{user_query}"
                
                【数据上下文】 {context_info}
                
                请拆解 2-4 个分析角度。每个角度的代码块将被依次执行。
                **注意**：
                1. 代码块之间共享上下文。如果角度2需要用到角度1计算的变量，确保变量名一致。
                2. **绝对禁止**导入 IPython 或使用 display() 函数。
                3. **避免 'ambiguous' 错误**：如果 index name 与 column name 冲突，请在 reset_index() 前先使用 `df.index.name = None` 或重命名索引。
                4. **避免 'Length mismatch' 错误**：禁止使用 `df.columns = [...]` 强行改名，必须使用 `df.rename(columns={{...}})`。
                5. 在代码开头，先检查前置依赖的变量是否存在，例如 `if 'df_filtered' not in locals(): result = pd.DataFrame()`。
                6. [重要] 每个角度的最终结果必须赋值给变量 `result` (例如 `result = df_grouped`)，否则无法展示。
                
                输出 JSON: {{ "intent_analysis": "...", "angles": [ {{ "title": "...", "desc": "...", "summary": {{ "intent": "...", "scope": "...", "metrics": "...", "key_match": "...", "logic": "..." }}, "code": "..." }} ] }}
                """
                resp_plan = safe_generate(client, MODEL_SMART, prompt_plan, "application/json")
                plan_json = clean_json_string(resp_plan.text)
            
            if plan_json:
                intro = f"### 1. 意图深度解析\n{plan_json.get('intent_analysis')}"
                st.markdown(intro)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": intro})
                
                angles_data = []
                st.markdown('<div class="step-header">2. 多维分析报告</div>', unsafe_allow_html=True)
                
                for angle in plan_json.get('angles', []):
                    with st.container():
                        st.markdown(f"**{angle['title']}**: {angle['desc']}")
                        
                        if 'summary' in angle:
                            render_protocol_card(angle['summary'])
                        
                        # 清除上一轮的 result，防止变量残留
                        if 'result' in shared_ctx: del shared_ctx['result']
                            
                        try:
                            exec(angle['code'], shared_ctx)
                            res_raw = shared_ctx.get('result')
                            
                            # 调试信息：如果读不到数据，在后台打印一下生成的代码，方便排查
                            if res_raw is None:
                                print(f"Warning: No 'result' variable found in code execution for angle: {angle['title']}")
                                print("Generated Code:", angle['code'])

                            res_df = normalize_result(res_raw)
                            
                            if not safe_check_empty(res_df):
                                formatted_df = format_display_df(res_df)
                                st.dataframe(formatted_df, use_container_width=True)
                                st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"**{angle['title']}**"})
                                st.session_state.messages.append({"role": "assistant", "type": "df", "content": formatted_df})
                                
                                prompt_mini = f"简要解读数据 (50字内):\n{res_df.to_string()}"
                                resp_mini = safe_generate(client, MODEL_FAST, prompt_mini)
                                explanation = resp_mini.text
                                st.markdown(f'<div class="mini-insight">💡 {explanation}</div>', unsafe_allow_html=True)
                                angles_data.append({"title": angle['title'], "explanation": explanation})
                            else:
                                st.warning(f"角度【{angle['title']}】无数据 (可能原因：筛选条件过严或代码未正确赋值 result)")
                        except Exception as e:
                            st.error(f"计算错误: {e}")
                            # 同样打印错误代码以便调试
                            print(f"Error in angle {angle['title']}: {e}")
                            print("Code:", angle['code'])

                if angles_data:
                    with st.spinner(f"📝 生成最终综述 ({MODEL_SMART})..."):
                        findings = "\n".join([f"[{a['title']}]: {a['explanation']}" for a in angles_data])
                        prompt_final = f"""基于发现回答: "{user_query}"\n【发现】{findings}\n生成 Markdown 总结。"""
                        resp_final = safe_generate(client, MODEL_SMART, prompt_final)
                        insight = resp_final.text
                        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"### 总结\n{insight}"})

                    # === Step 3. 智能追问推荐 (使用 on_click 修复版) ===
                    with st.spinner("🤔 正在思考后续追问..."):
                        prompt_next = f"""
                        基于以下分析结论和数据结构，推荐 2 个用户可能感兴趣的后续深度追问问题。
                        确保问题可以通过现有数据回答。简洁明了，不要编号。

                        【当前结论】
                        {insight}

                        【数据结构】
                        {context_info}

                        输出 JSON 列表: ["问题1", "问题2"]
                        """
                        resp_next = safe_generate(client, MODEL_FAST, prompt_next, "application/json")
                        next_questions = clean_json_string(resp_next.text)

                    # 渲染追问按钮
                    if isinstance(next_questions, list) and len(next_questions) > 0:
                        st.markdown("### 🧐 还可以继续追问")
                        c1, c2 = st.columns(2)
                        
                        # [关键修复] 使用 on_click 回调，确保点击事件能穿透 Rerun
                        c1.button(f"👉 {next_questions[0]}", use_container_width=True, on_click=handle_followup, args=(next_questions[0],))
                            
                        if len(next_questions) > 1:
                            c2.button(f"👉 {next_questions[1]}", use_container_width=True, on_click=handle_followup, args=(next_questions[1],))
        else:
            st.info("请询问数据相关问题。")
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": "请询问数据相关问题。"})



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

# -----------------------------------------------------------------------------
# 1. 配置 & CSS 注入 (DESIGN SYSTEM: CYBER-TECH)
# -----------------------------------------------------------------------------

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="ChatBI // NEURAL NEXUS", 
    layout="wide", 
    page_icon="💠", 
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
        <style>
        /* 引入科幻/科技感字体 */
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

        :root {
            /* Cyberpunk / Tech Palette */
            --tech-bg-dark: #050a14;
            --tech-panel-bg: rgba(16, 23, 41, 0.7);
            --tech-cyan: #00f3ff;
            --tech-blue: #0077be;
            --tech-purple: #bc13fe;
            --tech-text-main: #e0f7fa;
            --tech-text-dim: #94a3b8;
            --tech-border-glow: 0 0 10px rgba(0, 243, 255, 0.3);
            --tech-font-head: 'Rajdhani', sans-serif;
            --tech-font-mono: 'JetBrains Mono', monospace;
        }

        /* 全局背景与字体设置 */
        .stApp {
            background-color: var(--tech-bg-dark);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(0, 119, 190, 0.08), transparent 25%), 
                radial-gradient(circle at 85% 30%, rgba(188, 19, 254, 0.08), transparent 25%);
            font-family: var(--tech-font-head);
            color: var(--tech-text-main);
        }

        /* 隐藏 Streamlit 原生组件 */
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        footer { display: none !important; }

        /* ================= 顶部导航栏 (HUD 风格) ================= */
        .fixed-header-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 70px;
            background: rgba(5, 10, 20, 0.95);
            border-bottom: 1px solid rgba(0, 243, 255, 0.2);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            z-index: 999999;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 30px;
        }

        .nav-logo-area {
            display: flex; align-items: center; gap: 10px;
            color: var(--tech-cyan);
            font-family: var(--tech-font-mono);
            font-size: 20px;
            font-weight: 700;
            text-shadow: 0 0 8px var(--tech-cyan);
            letter-spacing: 2px;
        }
        
        .nav-center {
            display: flex; gap: 40px;
        }
        
        .nav-item {
            color: var(--tech-text-dim);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 5px 0;
            position: relative;
            transition: 0.3s;
        }
        
        .nav-item:hover, .nav-item.active {
            color: var(--tech-cyan);
            text-shadow: 0 0 5px var(--tech-cyan);
        }
        
        .nav-item.active::after {
            content: ''; position: absolute; bottom: -24px; left: 0; width: 100%; height: 2px;
            background: var(--tech-cyan);
            box-shadow: 0 0 10px var(--tech-cyan);
        }

        .nav-right-status {
            display: flex; align-items: center; gap: 15px;
            font-family: var(--tech-font-mono);
            font-size: 12px;
            color: var(--tech-cyan);
        }
        
        .status-dot {
            width: 8px; height: 8px; background: #00ff41;
            border-radius: 50%;
            box-shadow: 0 0 5px #00ff41;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.5; box-shadow: 0 0 0px #00ff41; }
            50% { opacity: 1; box-shadow: 0 0 10px #00ff41; }
            100% { opacity: 0.5; box-shadow: 0 0 0px #00ff41; }
        }

        /* ================= 布局调整 ================= */
        .block-container {
            padding-top: 100px !important;
            padding-bottom: 50px !important;
            max-width: 1400px;
        }

        /* ================= UI 组件样式 ================= */
        
        /* 按钮重写 */
        div.stButton > button {
            background: transparent !important;
            border: 1px solid var(--tech-cyan) !important;
            color: var(--tech-cyan) !important;
            font-family: var(--tech-font-mono) !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            border-radius: 2px;
        }
        div.stButton > button:hover {
            background: rgba(0, 243, 255, 0.1) !important;
            box-shadow: 0 0 15px var(--tech-cyan) !important;
            transform: translateY(-2px);
        }
        
        /* 输入框重写 */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: rgba(0,0,0,0.3) !important;
            border: 1px solid #334155 !important;
            color: var(--tech-text-main) !important;
            font-family: var(--tech-font-mono) !important;
        }
        .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
            border-color: var(--tech-cyan) !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
        }

        /* 卡片容器 */
        .tech-card {
            background: linear-gradient(135deg, rgba(16, 23, 41, 0.9) 0%, rgba(5, 10, 20, 0.95) 100%);
            border: 1px solid rgba(0, 243, 255, 0.3);
            border-left: 3px solid var(--tech-cyan);
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        /* 卡片扫描线效果 */
        .tech-card::after {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.5), transparent);
            animation: scanline 4s linear infinite;
        }

        @keyframes scanline {
            0% { top: -10%; opacity: 0; }
            20% { opacity: 1; }
            100% { top: 110%; opacity: 0; }
        }

        .angle-title {
            color: var(--tech-cyan);
            font-family: var(--tech-font-mono);
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            display: flex; align-items: center;
            margin-bottom: 10px;
        }
        .angle-title::before {
            content: '>> '; 
            margin-right: 8px;
            color: var(--tech-purple);
        }
        
        .angle-desc {
            color: var(--tech-text-dim);
            font-size: 14px;
            margin-bottom: 15px;
            border-bottom: 1px dashed rgba(148, 163, 184, 0.3);
            padding-bottom: 10px;
        }

        /* 摘要盒子 */
        .summary-box {
            background: rgba(188, 19, 254, 0.05);
            border: 1px solid var(--tech-purple);
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-family: var(--tech-font-mono);
            font-size: 13px;
        }
        .summary-title {
            color: var(--tech-purple);
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
            display: flex; align-items: center; gap: 8px;
        }
        .summary-list li {
            list-style: none;
            margin-bottom: 4px;
            color: var(--tech-text-dim);
        }
        .summary-label {
            color: var(--tech-text-main);
            font-weight: bold;
            margin-right: 8px;
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 2px;
        }

        /* 洞察盒子 */
        .insight-box {
            background: linear-gradient(90deg, rgba(0,243,255,0.05) 0%, transparent 100%);
            border-left: 4px solid var(--tech-cyan);
            padding: 20px;
            font-size: 15px;
            line-height: 1.6;
            color: var(--tech-text-main);
            position: relative;
        }
        .mini-insight {
            background: #0f172a;
            border: 1px solid #1e293b;
            padding: 10px;
            color: #94a3b8;
            font-size: 13px;
            margin-top: 10px;
            font-family: var(--tech-font-mono);
        }

        /* 步骤标题 */
        .step-header {
            color: var(--tech-text-main);
            font-size: 20px;
            font-weight: 700;
            margin: 40px 0 20px 0;
            text-transform: uppercase;
            letter-spacing: 2px;
            display: flex; align-items: center;
        }
        .step-header::before {
            content: 'II';
            margin-right: 15px;
            color: var(--tech-cyan);
            font-family: var(--tech-font-mono);
            background: rgba(0,243,255,0.1);
            padding: 2px 8px;
            font-size: 14px;
        }

        /* 侧边栏调整 */
        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            color: var(--tech-text-main);
            font-family: var(--tech-font-head);
        }
        
        /* 聊天气泡调整 */
        .stChatMessage {
            background-color: transparent !important;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        [data-testid="stChatMessageContent"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0px 12px 12px 12px !important;
            font-family: 'Inter', sans-serif;
        }
        /* 用户气泡特殊处理 */
        div[data-testid="chatAvatarIcon-user"] {
            background-color: var(--tech-purple) !important;
        }
        /* AI 气泡特殊处理 */
        div[data-testid="chatAvatarIcon-assistant"] {
            background-color: var(--tech-cyan) !important;
        }

        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 核心逻辑 (后端保持不变)
# -----------------------------------------------------------------------------

# --- 配置读取 ---
try:
    FIXED_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    FIXED_API_KEY = ""

FIXED_FILE_NAME = "hcmdata.xlsx" 
LOGO_FILE = "logo.png"

PREVIEW_ROW_LIMIT = 500
EXPORT_ROW_LIMIT = 5000   

@st.cache_resource
def get_client():
    if not FIXED_API_KEY: return None
    try:
        return genai.Client(api_key=FIXED_API_KEY, http_options={'api_version': 'v1beta'})
    except Exception as e:
        st.error(f"SDK INIT FAILED: {e}")
        return None

def safe_generate_content(client, model_name, contents, config=None, retries=3):
    base_delay = 5 
    for i in range(retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if i < retries - 1:
                    time.sleep(base_delay * (2 ** i))
                    continue
            raise e

@st.cache_data
def load_data():
    if not os.path.exists(FIXED_FILE_NAME):
        # 创建一个假数据用于演示
        data = {
            '省份': ['江苏', '浙江', '上海', '江苏', '浙江', '上海'],
            '产品': ['A', 'A', 'A', 'B', 'B', 'B'],
            'Date': ['2023Q1', '2023Q1', '2023Q1', '2023Q2', '2023Q2', '2023Q2'],
            'Sales_Value': [1000, 2000, 1500, 1100, 2100, 1600],
            'Qty': [100, 200, 150, 110, 210, 160]
        }
        return pd.DataFrame(data)

    try:
        if FIXED_FILE_NAME.endswith('.csv'):
            df = pd.read_csv(FIXED_FILE_NAME)
        else:
            df = pd.read_excel(FIXED_FILE_NAME)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty', '金额']):
                try:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '', regex=False),
                        errors='coerce'
                    ).fillna(0)
                except: pass
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return None

def get_history_context(messages, turn_limit=3):
    if len(messages) <= 1: return "无历史对话。"
    recent_msgs = messages[:-1]
    valid_msgs = [m for m in recent_msgs if m['type'] in ['text', 'report_block']]
    slice_start = max(0, len(valid_msgs) - (turn_limit * 2))
    target_msgs = valid_msgs[slice_start:]
    context_list = []
    for msg in target_msgs:
        role = "User" if msg['role'] == 'user' else "AI"
        content_str = ""
        if msg['type'] == 'text':
            content_str = msg['content']
        elif msg['type'] == 'report_block':
            data = msg['content']
            mode = data.get('mode', 'analysis')
            if mode == 'simple':
                s = data.get('summary', {})
                content_str = f"[History Data] Intent: {s.get('intent')}, Logic: {s.get('logic')}"
            else:
                intent = data.get('intent', '无意图')
                insight = data.get('insight', '无洞察')
                angles_summary = [f"<{a['title']}: {a['explanation']}>" for a in data.get('angles_data', [])]
                content_str = f"[History Analysis] Intent: {intent} | Findings: {'; '.join(angles_summary)} | Insight: {insight}"
        context_list.append(f"{role}: {content_str}")
    return "\n".join(context_list)

def analyze_time_structure(df):
    time_col = None
    for col in df.columns:
        if '年季' in col or 'Quarter' in col or 'Date' in col:
            sample = str(df[col].iloc[0])
            if 'Q' in sample and len(sample) <= 6:
                time_col = col; break
    if time_col:
        sorted_periods = sorted(df[time_col].unique().astype(str))
        max_q = sorted_periods[-1]
        min_q = sorted_periods[0]
        mat_list = sorted_periods[-4:] if len(sorted_periods) >= 4 else sorted_periods
        is_mat_complete = True
        mat_list_prior = []
        if len(sorted_periods) >= 8:
            mat_list_prior = sorted_periods[-8:-4]
        elif len(sorted_periods) >= 4:
            mat_list_prior = sorted_periods[:-4]
            is_mat_complete = False
        else:
            is_mat_complete = False
        ytd_list, ytd_list_prior = [], []
        import re
        year_match = re.search(r'(\d{4})', str(max_q))
        if year_match:
            curr_year = year_match.group(1)
            try:
                prev_year = str(int(curr_year) - 1)
                ytd_list = [p for p in sorted_periods if curr_year in str(p)]
                expected_priors = [str(p).replace(curr_year, prev_year) for p in ytd_list]
                ytd_list_prior = [p for p in sorted_periods if p in expected_priors]
            except: pass
        return {
            "col_name": time_col, "all_periods": sorted_periods, "max_q": max_q, "min_q": min_q, 
            "mat_list": mat_list, "mat_list_prior": mat_list_prior, "is_mat_complete": is_mat_complete,
            "ytd_list": ytd_list, "ytd_list_prior": ytd_list_prior
        }
    return {"error": "No Time Column Found"}

def build_metadata(df, time_context):
    info = []
    info.append(f"【Time Col】: {time_context.get('col_name')}")
    info.append(f"【Current MAT】: {time_context.get('mat_list')}")
    info.append(f"【Current YTD】: {time_context.get('ytd_list')}")
    for col in df.columns:
        dtype = str(df[col].dtype)
        uniques = df[col].dropna().unique()
        desc = f"- `{col}` ({dtype})"
        if dtype == 'object' or len(uniques) < 2000:
            vals = list(uniques[:5]) if len(uniques) > 100 else list(uniques)
            desc += f" | EX: {vals}"
        info.append(desc)
    return "\n".join(info)

def normalize_result(res):
    if isinstance(res, pd.DataFrame): return res
    if isinstance(res, pd.Series): return res.to_frame()
    if isinstance(res, dict):
        try: return pd.DataFrame(list(res.items()), columns=['指标', '数值'])
        except: pass
    try: return pd.DataFrame([res])
    except: return pd.DataFrame({"Result": [str(res)]})

def format_df_for_display(df_raw):
    if not isinstance(df_raw, pd.DataFrame): return df_raw
    df_fmt = df_raw.copy()
    percent_keywords = ['Rate', 'Ratio', 'Share', 'Percent', 'Pct', 'YoY', 'CAGR', '率', '比', '占比', '份额']
    exclude_keywords = ['Value', 'Amount', 'Qty', 'Volume', 'Contribution', 'Abs', '额', '量']
    for col in df_fmt.columns:
        if pd.api.types.is_numeric_dtype(df_fmt[col]):
            col_str = str(col)
            is_percent = any(k in col_str for k in percent_keywords)
            has_exclude = any(k in col_str for k in exclude_keywords)
            if is_percent and not has_exclude:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "-")
            else:
                is_integer = False
                try:
                    if (df_fmt[col].dropna() % 1 == 0).all(): is_integer = True
                except: pass
                fmt = "{:,.0f}" if is_integer else "{:,.2f}"
                df_fmt[col] = df_fmt[col].apply(lambda x: fmt.format(x) if pd.notnull(x) else "-")
    return df_fmt

def parse_response(text):
    reasoning = text
    json_data = None
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            potential_json = text[start_idx : end_idx + 1]
            try:
                json_data = json.loads(potential_json)
                reasoning = text[:start_idx].strip()
            except json.JSONDecodeError: pass
    except Exception: pass
    return reasoning, json_data

# -----------------------------------------------------------------------------
# 3. 页面渲染 (Front-End Components)
# -----------------------------------------------------------------------------

def render_header_nav():
    logo_b64 = ""
    # 尝试加载 Logo
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:30px; margin-right:10px;">' if logo_b64 else '<span style="font-size:24px; margin-right:5px;">🧬</span>'

    # Tech Header HTML
    nav_html = f"""
    <div class="fixed-header-container">
        <div class="nav-logo-area">
            {logo_html}
            <span>CHAT<span style="color:#fff;">BI</span></span>
        </div>
        <div class="nav-center">
            <div class="nav-item">DASHBOARD</div> 
            <div class="nav-item active">INTELLIGENCE</div>
            <div class="nav-item">REPORTS</div>
        </div>
        <div class="nav-right-status">
            <div class="status-dot"></div>
            <span>SYSTEM ONLINE</span>
            <span style="color:var(--tech-text-dim);">|</span>
            <span>USER: PRO_ADMIN</span>
            <button onclick="alert('CONNECTION TERMINATED')" style="background:transparent; border:1px solid #334155; color:#94a3b8; padding:4px 12px; margin-left:10px; cursor:pointer;">EXIT</button>
        </div>
    </div>
    """
    st.markdown(nav_html.replace("\n", ""), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 主程序 (Main Execution)
# -----------------------------------------------------------------------------

inject_custom_css()
render_header_nav()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_query_draft" not in st.session_state:
    st.session_state.last_query_draft = ""
if "is_interrupted" not in st.session_state:
    st.session_state.is_interrupted = False

client = get_client()

if not client:
    st.warning("⚠️ API KEY MISSING. PLEASE CONFIGURE SECRETS.")
    st.stop()

df = load_data()

if df is not None:
    time_context = analyze_time_structure(df)
    meta_data = build_metadata(df, time_context)
    
    # --- Sidebar: Control Panel ---
    with st.sidebar:
        st.markdown("### 🛠️ CONTROL PANEL")
        st.caption("CONNECTION: SECURE")
        
        st.markdown(f"""
        <div style="background:#0f172a; padding:10px; border-left:2px solid #00f3ff; margin-bottom:10px;">
            <div style="font-size:12px; color:#94a3b8;">DATA ROWS</div>
            <div style="font-size:18px; color:#fff; font-family:var(--tech-font-mono);">{len(df):,}</div>
        </div>
        <div style="background:#0f172a; padding:10px; border-left:2px solid #bc13fe; margin-bottom:20px;">
            <div style="font-size:12px; color:#94a3b8;">TIME SPAN</div>
            <div style="font-size:14px; color:#fff; font-family:var(--tech-font-mono);">{time_context.get('min_q')} >> {time_context.get('max_q')}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ PURGE MEMORY", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_query_draft = ""
            st.session_state.is_interrupted = False
            st.rerun()

    # --- Chat Render ---
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            elif msg["type"] == "report_block":
                content = msg["content"]
                mode = content.get('mode', 'analysis') 
                
                if mode == 'simple':
                    if 'summary' in content:
                        s = content['summary']
                        st.markdown(f"""
                        <div class="summary-box">
                            <div class="summary-title">⚡ EXECUTION PROTOCOL</div>
                            <ul class="summary-list">
                                <li><span class="summary-label">INTENT</span> {s.get('intent', '-')}</li>
                                <li><span class="summary-label">METRIC</span> {s.get('metrics', '-')}</li>
                                <li><span class="summary-label">LOGIC</span> {s.get('logic', '-')}</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.success("DATA EXTRACTION COMPLETE")
                    
                    if 'data' in content:
                        data_payload = content['data']
                        if isinstance(data_payload, pd.DataFrame):
                            data_payload = {"RESULT": data_payload}
                        
                        for table_name, table_df in data_payload.items():
                            if len(data_payload) > 1: st.markdown(f"**📄 {table_name}**")
                            # 强制使用 Streamlit 的 dataframe，但外部容器已经变黑
                            st.dataframe(format_df_for_display(table_df).head(PREVIEW_ROW_LIMIT), use_container_width=True)
                            
                            csv = table_df.head(EXPORT_ROW_LIMIT).to_csv(index=False).encode('utf-8-sig')
                            st.download_button(f"📥 EXPORT CSV ({table_name})", csv, f"{table_name}.csv", "text/csv", key=f"dl_simple_{msg_idx}_{table_name}")

                else:
                    st.markdown('<div class="step-header">01 // INTENT PARSING</div>', unsafe_allow_html=True)
                    st.markdown(content.get('intent', ''))
                    
                    if 'angles_data' in content:
                        st.markdown('<div class="step-header">02 // MULTI-VECTOR ANALYSIS</div>', unsafe_allow_html=True)
                        for i, angle in enumerate(content['angles_data']):
                            with st.container():
                                st.markdown(f"""
                                <div class="tech-card">
                                    <div class="angle-title">{angle['title']}</div>
                                    <div class="angle-desc">{angle['desc']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.dataframe(format_df_for_display(angle['data']).head(PREVIEW_ROW_LIMIT), use_container_width=True)
                                
                                csv = angle['data'].head(EXPORT_ROW_LIMIT).to_csv(index=False).encode('utf-8-sig')
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.download_button(f"📥 DOWNLOAD", csv, f"angle_{i}_hist.csv", "text/csv", key=f"dl_hist_{msg_idx}_{i}")
                                st.markdown(f'<div class="mini-insight">💡 <b>DEEP DIVE:</b> {angle["explanation"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="step-header">03 // SYNTHESIZED INSIGHT</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="insight-box">{content.get("insight", "")}</div>', unsafe_allow_html=True)

    # --- Suggestion Chips ---
    if len(st.session_state.messages) == 0 and not st.session_state.is_interrupted:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:var(--tech-cyan); margin-bottom:20px; font-family:var(--tech-font-mono)'>// INITIATE QUERY SEQUENCE</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        q1, q2, q3 = "What is the market share by province?", "Which products have high YoY growth?", "Analyze regional performance trends."
        if col1.button(f"🗺️ **MARKET SHARE**\n\n{q1}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "type": "text", "content": q1}); st.rerun()
        if col2.button(f"📈 **GROWTH RATE**\n\n{q2}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "type": "text", "content": q2}); st.rerun()
        if col3.button(f"📊 **REGIONAL TREND**\n\n{q3}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "type": "text", "content": q3}); st.rerun()

    # --- Input Area ---
    if st.session_state.is_interrupted:
        st.warning("⚠️ PROCESS ABORTED. REVISE INPUT:")
        def submit_edit():
            new_val = st.session_state["edit_input_widget"]
            if new_val:
                st.session_state.messages.append({"role": "user", "type": "text", "content": new_val})
                st.session_state.is_interrupted = False
                st.session_state.last_query_draft = ""
        st.text_area("EDIT COMMAND", value=st.session_state.last_query_draft, key="edit_input_widget", height=100)
        st.button("🚀 RESUBMIT", on_click=submit_edit, type="primary")

    if not st.session_state.is_interrupted:
        if query_input := st.chat_input("🔎 ENTER COMMAND..."):
            st.session_state.last_query_draft = query_input
            st.session_state.messages.append({"role": "user", "type": "text", "content": query_input})
            st.rerun()

    # --- AI Processing Logic ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and not st.session_state.is_interrupted:
        current_query = st.session_state.messages[-1]["content"]
        history_context_str = get_history_context(st.session_state.messages, turn_limit=3)
        stop_btn_placeholder = st.empty()
        
        if stop_btn_placeholder.button("⏹️ ABORT SEQUENCE", type="primary", use_container_width=True):
            st.session_state.is_interrupted = True; st.rerun()

        with st.chat_message("assistant"):
            try:
                # 意图识别
                intent_type = "analysis" 
                with st.spinner("🔄 PARSING INTENT..."):
                    router_prompt = f"""
                    Based on user query: "{current_query}" and history.
                    【History】:{history_context_str}
                    Classify into:
                    1. "simple": Simple data retrieval, sorting, ranking, basic calc.
                    2. "analysis": Open-ended, insight seeking, market pattern.
                    3. "irrelevant": Chit-chat not related to data.
                    Output JSON: {{"type": "simple" OR "analysis" OR "irrelevant"}}
                    """
                    router_resp = safe_generate_content(
                        client, "gemini-2.0-flash", router_prompt, config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    try: intent_type = json.loads(router_resp.text).get('type', 'analysis')
                    except: intent_type = 'analysis'

                mat_list = time_context.get('mat_list')
                mat_list_prior = time_context.get('mat_list_prior')
                ytd_list = time_context.get('ytd_list')
                ytd_list_prior = time_context.get('ytd_list_prior')

                if intent_type == 'irrelevant':
                    st.warning("⚠️ OUT OF SCOPE")
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": "Query unrelated to dataset coverage."})

                # ================= [Simple Mode] =================
                elif intent_type == 'simple':
                    with st.spinner("⚡ GENERATING CODE BLOCK..."):
                        simple_prompt = f"""
                        You are a Pandas Expert. User Request: "{current_query}"
                        【Meta】{meta_data}
                        【History】{history_context_str}
                        【Time】MAT: {mat_list}, YTD: {ytd_list}
                        
                        【RULES】
                        1. Data source: `df` only.
                        2. Filter explicitly (e.g., `df[df['Province']=='Hainan']`).
                        3. Assign result dict to `results`.
                        4. NO PLOTTING.
                        
                        Output JSON: {{ 
                            "summary": {{ "intent": "desc", "metrics": "list", "logic": "desc" }}, 
                            "code": "df_sub = df[...]\nresults = {{'Title': df_sub}}" 
                        }}
                        """
                        simple_resp = safe_generate_content(
                            client, "gemini-2.0-flash", simple_prompt, config=types.GenerateContentConfig(response_mime_type="application/json")
                        )
                        simple_json = json.loads(simple_resp.text)
                        
                        execution_context = {
                            'df': df, 'pd': pd, 'np': np, 'results': {}, 'result': None,
                            'current_mat': mat_list, 'mat_list': mat_list, 'prior_mat': mat_list_prior,
                            'mat_list_prior': mat_list_prior, 'ytd_list': ytd_list, 'ytd_list_prior': ytd_list_prior
                        }
                        exec(simple_json['code'], execution_context)
                        
                        final_results = execution_context.get('results')
                        if not final_results and execution_context.get('result') is not None:
                            final_results = {"RESULT": execution_context.get('result')}
                        
                        if final_results:
                            formatted_results = {k: normalize_result(v) for k, v in final_results.items()}
                            s = simple_json.get('summary', {})
                            
                            st.markdown(f"""
                            <div class="summary-box">
                                <div class="summary-title">⚡ EXECUTION PROTOCOL</div>
                                <ul class="summary-list">
                                    <li><span class="summary-label">INTENT</span> {s.get('intent','-')}</li>
                                    <li><span class="summary-label">LOGIC</span> {s.get('logic','-')}</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            for table_name, table_df in formatted_results.items():
                                if len(formatted_results) > 1: st.markdown(f"**📄 {table_name}**")
                                st.dataframe(format_df_for_display(table_df).head(PREVIEW_ROW_LIMIT), use_container_width=True)
                                csv = table_df.head(EXPORT_ROW_LIMIT).to_csv(index=False).encode('utf-8-sig')
                                st.download_button(f"📥 EXPORT ({table_name})", csv, f"{table_name}.csv", "text/csv", key=f"dl_simple_{len(st.session_state.messages)}_{table_name}")
                            
                            st.session_state.messages.append({
                                "role": "assistant", "type": "report_block",
                                "content": { "mode": "simple", "summary": s, "data": formatted_results }
                            })
                        else:
                            st.error("DATA EXTRACTION FAILED")
                            st.session_state.messages.append({"role": "assistant", "type": "text", "content": "No data found."})

                # ================= [Analysis Mode] =================
                else:
                    with st.spinner("🧠 DECOMPOSING QUERY..."):
                        prompt_plan = f"""
                        Role: BI Expert. Breakdown: "{current_query}" into 2-5 angles.
                        Combine Time(MAT/YTD) & Competition.
                        
                        【Meta】{meta_data}
                        【History】{history_context_str}
                        【Time】MAT: {mat_list}, YTD: {ytd_list}
                        
                        【RULES】
                        1. `df` is the only source.
                        2. Define all variables explicitly.
                        3. Assign final df to `result`.
                        4. Language: Chinese.
                        
                        Output JSON: {{ "intent_analysis": "Markdown analysis", "angles": [ {{"title": "Title", "description": "Desc", "code": "..."}} ] }}
                        """
                        response_plan = safe_generate_content(client, "gemini-2.0-flash", prompt_plan, config=types.GenerateContentConfig(response_mime_type="application/json"))
                        reasoning_text, plan_json = parse_response(response_plan.text)

                    if plan_json and 'angles' in plan_json:
                        st.markdown('<div class="step-header">01 // INTENT PARSING</div>', unsafe_allow_html=True)
                        st.markdown(plan_json.get('intent_analysis', 'Auto Analysis'))
                        
                        angles_data = [] 
                        st.markdown('<div class="step-header">02 // MULTI-VECTOR ANALYSIS</div>', unsafe_allow_html=True)
                        
                        for i, angle in enumerate(plan_json['angles']):
                            with st.container():
                                st.markdown(f"""
                                <div class="tech-card">
                                    <div class="angle-title">{angle['title']}</div>
                                    <div class="angle-desc">{angle.get('description','')}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                try:
                                    execution_context = {
                                        'df': df, 'pd': pd, 'np': np, 'result': None,
                                        'current_mat': mat_list, 'mat_list': mat_list, 'prior_mat': mat_list_prior,
                                        'mat_list_prior': mat_list_prior, 'ytd_list': ytd_list, 'ytd_list_prior': ytd_list_prior
                                    }
                                    exec(angle['code'], execution_context)
                                    
                                    if execution_context.get('result') is None:
                                        for k, v in list(execution_context.items()):
                                            if isinstance(v, pd.DataFrame) and k != 'df':
                                                execution_context['result'] = v; break
                                    
                                    if execution_context.get('result') is not None:
                                        res_df = normalize_result(execution_context['result'])
                                        st.dataframe(format_df_for_display(res_df).head(PREVIEW_ROW_LIMIT), use_container_width=True)
                                        
                                        with st.spinner(f"⚡ ANALYZING VECTOR {i+1}..."):
                                            mini_prompt = f"""
                                            Interpret this data (200 chars).
                                            Data:\n{res_df.head(20).to_string()}
                                            Req: Professional, Business Insight.
                                            """
                                            mini_resp = safe_generate_content(client, "gemini-2.0-flash", mini_prompt)
                                            explanation = mini_resp.text
                                            st.markdown(f'<div class="mini-insight">💡 <b>DEEP DIVE:</b> {explanation}</div>', unsafe_allow_html=True)
                                        
                                        angles_data.append({
                                            "title": angle['title'], "desc": angle.get('description',''),
                                            "data": res_df, "explanation": explanation
                                        })
                                    else:
                                        st.error("NO DATA RETURNED")
                                except Exception as e:
                                    st.error(f"CODE EXEC ERROR: {e}")

                        if angles_data:
                            st.markdown('<div class="step-header">03 // SYNTHESIZED INSIGHT</div>', unsafe_allow_html=True)
                            with st.spinner("🤖 SYNTHESIZING..."):
                                all_findings = "\n".join([f"[{ad['title']}]: {ad['explanation']}" for ad in angles_data])
                                final_prompt = f"""
                                Query: "{current_query}"
                                Findings: {all_findings}
                                Generate Final Insight (Markdown). No advice, just facts.
                                """
                                resp_final = safe_generate_content(client, "gemini-2.0-flash", final_prompt)
                                insight_text = resp_final.text
                                st.markdown(f'<div class="insight-box">{insight_text}</div>', unsafe_allow_html=True)
                                
                                st.session_state.messages.append({
                                    "role": "assistant", "type": "report_block",
                                    "content": {
                                        "mode": "analysis", "intent": plan_json.get('intent_analysis', ''),
                                        "angles_data": angles_data, "insight": insight_text
                                    }
                                })
                    else:
                        st.error("PLAN GENERATION FAILED")
            except Exception as e:
                st.error(f"SYSTEM FAILURE: {e}")
            finally:
                stop_btn_placeholder.empty()

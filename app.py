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
# 如果您确实有内测权限，请将 MODEL_SMART 改为 "gemini-3-pro-preview"
MODEL_FAST = "gemini-2.0-flash-exp"       # 路由 & 简单洞察
MODEL_SMART = "gemini-3-pro-preview"            # 写代码 & 深度分析 (原 gemini-3-pro-preview)

# --- 常量定义 ---
JOIN_KEY = "药品编码"
LOGO_FILE = "logo.png"

# --- 本地文件名定义 (请确保根目录有这两个文件) ---
FILE_FACT = "fact.xlsx"  # 销售事实表
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

        /* =================================================================
           1. 侧边栏控制按钮修复 (核心部分)
           ================================================================= */
        
        /* A. 展开按钮 (当侧边栏关闭时显示) */
        [data-testid="stSidebarCollapsedControl"] {
            display: block !important;
            position: fixed !important;
            top: 16px !important;       /* 调整垂直位置以对齐自定义Header */
            left: 16px !important;
            z-index: 1000002 !important; /* 最高层级，压在自定义Header上面 */
            color: var(--pc-text-sub) !important;
            background-color: transparent !important;
            width: 32px;
            height: 32px;
        }
        [data-testid="stSidebarCollapsedControl"]:hover {
            color: var(--pc-primary-blue) !important;
            background-color: #F0F7FF !important;
            border-radius: 4px;
        }

        /* B. 顶部 Header (包含收起按钮 X) */
        /* 不要 display:none，而是透明化，为了保留里面的 X 按钮 */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 1000001 !important; /* 保证在自定义Header之上 */
            height: 64px !important;
        }

        /* 隐藏 Header 里的右侧菜单 (三道杠) 和 部署按钮 */
        [data-testid="stToolbar"], 
        [data-testid="stHeaderActionElements"] {
            display: none !important;
        }
        
        /* 隐藏 Header 顶部的彩虹条 */
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* 确保 Header 里的按钮（收起 X）是可见的并且颜色正确 */
        header[data-testid="stHeader"] button {
            color: var(--pc-text-sub) !important;
        }
        header[data-testid="stHeader"] button:hover {
            color: var(--pc-primary-blue) !important;
            background-color: transparent !important;
        }

        /* =================================================================
           2. 自定义导航栏样式
           ================================================================= */
        .fixed-header-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 64px;
            background-color: #FFFFFF;
            box-shadow: 0 2px 12px rgba(0, 90, 222, 0.08);
            z-index: 999999; /* 比原生Header低一层，被它盖住，但原生Header是透明的 */
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; border-bottom: 1px solid #E6EBF5;
            padding-left: 60px; /* 【关键】左侧留出空隙给展开/收起按钮 */
        }
        
        /* 调整 Logo 位置，不要离按钮太近 */
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

        /* Streamlit 按钮样式美化 */
        div.stButton > button { border: 1px solid #E6EBF5; color: var(--pc-text-main); background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
        div.stButton > button:hover { border-color: var(--pc-primary-blue); color: var(--pc-primary-blue); background-color: #F0F7FF; }
        
        /* 报告框样式 */
        .summary-box {
            background-color: #FFFFFF; padding: 20px; border-radius: 8px;
            border: 1px solid #E6EBF5; border-left: 4px solid var(--pc-primary-blue); margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .summary-title { font-weight: 700; color: var(--pc-text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-size: 15px; }
        .summary-list li { margin-bottom: 8px; color: var(--pc-text-main); font-size: 14px; line-height: 1.6; }
        .summary-label { font-weight: 600; color: var(--pc-text-sub); margin-right: 8px; background: #F4F6F9; padding: 2px 6px; border-radius: 4px; font-size: 12px; }

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
            font-size: 13px; color: var(--pc-text-main); margin-top: 15px; 
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
            font-weight: 700; color: var(--pc-text-main); font-size: 16px; margin-top: 35px; 
            margin-bottom: 20px; display: flex; align-items: center;
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

# --- 修改：从本地加载数据 ---
@st.cache_data
def load_local_data(filename):
    """从根目录加载数据"""
    if not os.path.exists(filename):
        return None
    try:
        if filename.endswith('.csv'): df = pd.read_csv(filename)
        else: df = pd.read_excel(filename)
        df.columns = df.columns.str.strip()
        
        # 强制清洗关联键
        if JOIN_KEY in df.columns:
            df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
        for col in df.columns:
            # 自动识别数值列
            if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty']):
                try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                except: pass
            # 自动识别日期列
            if any(k in str(col).lower() for k in ['日期', 'date', 'time', '月份']):
                try: df[col] = pd.to_datetime(df[col])
                except: pass
                
        return df
    except Exception as e: 
        st.error(f"加载 {filename} 失败: {e}")
        return None

def get_dataframe_info(df, name="df"):
    if df is None: return f"{name}: 未加载"
    info = [f"### 表名: `{name}` ({len(df)} 行)"]
    info.append("| 列名 | 类型 | 示例值 (Top 20 枚举) |")
    info.append("|---|---|---|")
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        if df[col].dtype == 'object' or 'category' in str(df[col].dtype):
            uniques = df[col].dropna().unique()
            sample = list(uniques[:20]) 
            example_str = str(sample)
        else:
            try: example_str = f"{df[col].min()} ~ {df[col].max()}"
            except: example_str = "数值"
        
        if len(example_str) > 200: example_str = example_str[:200] + "..."
        info.append(f"| {col} | {dtype} | {example_str} |")
    
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
    try: return client.models.generate_content(model=model, contents=prompt, config=config)
    except Exception as e: return type('obj', (object,), {'text': f"Error: {e}"})

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

def normalize_result(res):
    """万能结果转换"""
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

# ================= 4. 页面渲染 =================

inject_custom_css()
client = get_client()

# --- 加载数据 (根目录) ---
# 确保在侧边栏渲染前加载数据
df_sales = load_local_data(FILE_FACT)
df_product = load_local_data(FILE_DIM)

# --- Header 渲染 ---
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

# --- Sidebar (修改版) ---
with st.sidebar:
    st.markdown("### 📊 数据概览")
    
    if df_sales is not None:
        st.success(f"已加载: {FILE_FACT}")
        
        # 1. 显示时间范围
        date_cols = df_sales.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        if len(date_cols) > 0:
            target_col = date_cols[0]
            min_date = df_sales[target_col].min()
            max_date = df_sales[target_col].max()
            st.info(f"**时间范围 ({target_col})**:\n\n{min_date.date()} 至 {max_date.date()}")
        else:
            st.caption("未检测到时间字段")
            
        st.divider()
        
        # 2. 显示字段
        st.markdown("**包含字段:**")
        st.dataframe(pd.DataFrame(df_sales.columns, columns=["Fact字段"]), height=150, hide_index=True)
    else:
        st.error(f"未找到 {FILE_FACT}")
        st.caption("请将文件放入项目根目录")

    if df_product is not None:
        st.success(f"已加载: {FILE_DIM}")
        st.dataframe(pd.DataFrame(df_product.columns, columns=["Dim字段"]), height=150, hide_index=True)
    else:
        st.error(f"未找到 {FILE_DIM}")

    st.divider()
    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Chat History (渲染逻辑) ---
# 这一步非常重要，确保每次 rerun 时历史记录都会被重新画出来
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text": st.markdown(msg["content"])
        elif msg["type"] == "df": st.dataframe(msg["content"], use_container_width=True)

# --- 猜你想问 ---
if not st.session_state.messages:
    st.markdown("### 💡 猜你想问")
    c1, c2, c3 = st.columns(3)
    if c1.button("🗺️ 康缘在各省份的份额?"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "康缘在各省份的份额?"}); st.rerun()
    if c2.button("💊 查一下泰中定的销售额"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "查一下泰中定的销售额"}); st.rerun()
    if c3.button("📊 市场增长趋势分析"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "分析一下市场增长趋势"}); st.rerun()

# --- Input ---
if query := st.chat_input("🔎 请输入问题..."):
    # 立即上屏并保存用户问题
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "type": "text", "content": query})
    
    # 触发处理逻辑
    with st.chat_message("assistant"):
        if df_sales is None or df_product is None:
            st.error(f"请确保根目录下存在 {FILE_FACT} 和 {FILE_DIM}")
            st.stop()

        context_info = f"""
        {get_dataframe_info(df_sales, "df_sales")}
        {get_dataframe_info(df_product, "df_product")}
        关联键: `{JOIN_KEY}`
        """

        # 1. 意图识别
        with st.status("🔄 思考中...", expanded=False) as status:
            prompt_router = f"""
            判断用户意图: "{query}"
            输出 JSON: {{ "type": "simple/analysis/irrelevant" }}
            """
            resp = safe_generate(client, MODEL_FAST, prompt_router, "application/json")
            intent = clean_json_string(resp.text).get('type', 'simple')
            status.update(label=f"意图: {intent.upper()}", state="complete")

        # 2. 简单查询 (Simple)
        if intent == 'simple':
            with st.spinner(f"⚡ 正在生成代码 ({MODEL_SMART})..."):
                prompt_code = f"""
                你是一位 Python 专家。
                用户问题: "{query}"
                
                【数据上下文 (含枚举)】
                {context_info}
                
                【严格指令】
                1. 如果用户问“有哪些产品”，**不要按名称过滤**，直接返回 `df_product` 的前 20 行。
                2. 如果涉及销量，必须使用 `pd.merge` 关联两表。
                3. **容错机制**: 关联结果为空时，请勿报错，而是返回空表。
                4. 结果赋值给 `result`。
                
                输出 JSON: {{ "summary": {{ "intent": "...", "metrics": "...", "logic": "..." }}, "code": "..." }}
                """
                resp_code = safe_generate(client, MODEL_SMART, prompt_code, "application/json")
                plan = clean_json_string(resp_code.text)
            
            if plan:
                s = plan.get('summary', {})
                st.markdown(f"""
                <div class="summary-box">
                    <div class="summary-title">⚡ 取数执行协议</div>
                    <ul class="summary-list">
                        <li><span class="summary-label">意图</span> {s.get('intent', '-')}</li>
                        <li><span class="summary-label">指标</span> {s.get('metrics', '-')}</li>
                        <li><span class="summary-label">逻辑</span> {s.get('logic', '-')}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                # 保存这个摘要到历史记录（作为 Text）
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"**执行协议**: {s.get('intent', '-')}"})

                exec_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np, "result": None}
                
                try:
                    exec(plan['code'], exec_ctx)
                    res_raw = exec_ctx.get('result')
                    
                    if res_raw is not None:
                        res_df = normalize_result(res_raw)
                        
                        if not safe_check_empty(res_df):
                            st.dataframe(format_display_df(res_df), use_container_width=True)
                            # 保存 DF 到历史记录
                            st.session_state.messages.append({"role": "assistant", "type": "df", "content": format_display_df(res_df)})
                        else:
                            st.warning("⚠️ 关联查询结果为空，尝试模糊搜索产品库...")
                            fallback_code = f"result = df_product[df_product.astype(str).apply(lambda x: x.str.contains('{query[:2]}', case=False)).any(axis=1)].head(10)"
                            try:
                                exec(fallback_code, exec_ctx)
                                res_fallback = normalize_result(exec_ctx.get('result'))
                                if not safe_check_empty(res_fallback):
                                    st.dataframe(res_fallback)
                                    st.session_state.messages.append({"role": "assistant", "type": "df", "content": res_fallback})
                                else:
                                    msg = "在产品库中也未找到相关信息。"
                                    st.error(msg)
                                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": msg})
                            except:
                                st.error("查询无结果。")
                    else:
                         st.error("代码未返回结果变量。")
                except Exception as e:
                    st.error(f"代码错误: {e}")

        # 3. 深度分析 (Analysis)
        elif intent == 'analysis':
            # Step 1: 拆解角度
            with st.spinner(f"🧠 专家拆解分析思路 ({MODEL_SMART})..."):
                prompt_plan = f"""
                你是一位医药行业高级分析师。
                用户问题: "{query}"
                
                【数据上下文 (含枚举)】
                {context_info}
                
                请将问题拆解为 2-4 个分析角度。每个角度生成一段 Python 代码计算数据。
                输出 JSON: {{ 
                    "intent_analysis": "整体分析思路...", 
                    "angles": [ 
                        {{ "title": "维度1", "desc": "描述", "code": "result=..." }} 
                    ] 
                }}
                """
                resp_plan = safe_generate(client, MODEL_SMART, prompt_plan, "application/json")
                plan_json = clean_json_string(resp_plan.text)
            
            if plan_json:
                analysis_intro = f"### 1. 意图深度解析\n{plan_json.get('intent_analysis')}"
                st.markdown(analysis_intro)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": analysis_intro})
                
                angles_data = []
                st.markdown('<div class="step-header">2. 多维分析报告</div>', unsafe_allow_html=True)
                
                # Step 2: 循环执行角度
                for angle in plan_json.get('angles', []):
                    with st.container():
                        st.markdown(f"**{angle['title']}**: {angle['desc']}")
                        
                        exec_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np, "result": None}
                        try:
                            exec(angle['code'], exec_ctx)
                            res_raw = exec_ctx.get('result')
                            res_df = normalize_result(res_raw)
                            
                            if not safe_check_empty(res_df):
                                st.dataframe(format_display_df(res_df), use_container_width=True)
                                # 保存中间结果到历史
                                st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"**{angle['title']}**"})
                                st.session_state.messages.append({"role": "assistant", "type": "df", "content": format_display_df(res_df)})
                                
                                prompt_mini = f"简要解读数据趋势 (50字内):\n{res_df.to_string()}"
                                resp_mini = safe_generate(client, MODEL_FAST, prompt_mini)
                                explanation = resp_mini.text
                                st.markdown(f'<div class="mini-insight">💡 {explanation}</div>', unsafe_allow_html=True)
                                
                                angles_data.append({
                                    "title": angle['title'], "desc": angle['desc'], 
                                    "data": res_df, "explanation": explanation
                                })
                            else:
                                st.warning(f"角度【{angle['title']}】无数据")
                        except Exception as e:
                            st.error(f"计算错误: {e}")

                # Step 4: 全局总结
                if angles_data:
                    with st.spinner(f"📝 生成最终综述 ({MODEL_SMART})..."):
                        findings = "\n".join([f"[{a['title']}]: {a['explanation']}" for a in angles_data])
                        prompt_final = f"""
                        基于各角度发现回答问题: "{query}"
                        
                        【各角度发现】
                        {findings}
                        
                        生成一段专业的 Markdown 总结，不包含建议，仅陈述事实。
                        """
                        resp_final = safe_generate(client, MODEL_SMART, prompt_final)
                        insight_text = resp_final.text
                        st.markdown(f'<div class="insight-box">{insight_text}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"### 总结\n{insight_text}"})

        else:
            st.info("请询问与数据相关的问题。")




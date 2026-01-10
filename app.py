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

# --- [修正] 模型配置：严格遵循指令 ---
# 1. 路由 & 简单响应 -> Flash 2.0
MODEL_FAST = "gemini-2.0-flash-exp"       

# 2. 复杂逻辑 & 代码生成 & 总结 -> 1.5 Pro (对应您要求的强推理 3pro)
MODEL_SMART = "gemini-3-pro-preview"            

# --- 常量定义 ---
JOIN_KEY = "药品编码"
LOGO_FILE = "logo.png"

try:
    FIXED_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    FIXED_API_KEY = ""

# ================= 2. 视觉体系 (VI) 核心代码 =================

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

        /* 顶部导航栏 */
        .fixed-header-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 64px;
            background-color: #FFFFFF;
            box-shadow: 0 2px 12px rgba(0, 90, 222, 0.08);
            z-index: 999999; display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; border-bottom: 1px solid #E6EBF5;
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
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        footer { display: none !important; }

        /* 组件风格 */
        div.stButton > button { border: 1px solid #E6EBF5; color: var(--pc-text-main); background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
        div.stButton > button:hover { border-color: var(--pc-primary-blue); color: var(--pc-primary-blue); background-color: #F0F7FF; }
        
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

@st.cache_data
def load_data_from_upload(file_obj, file_type):
    if file_obj is None: return None
    try:
        if file_obj.name.endswith('.csv'): df = pd.read_csv(file_obj)
        else: df = pd.read_excel(file_obj)
        df.columns = df.columns.str.strip()
        
        # 【关键修复】强制清洗关联键
        if JOIN_KEY in df.columns:
            # 转字符串 -> 去空格 -> 去除 .0 后缀 (例如 "1001.0" -> "1001")
            df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
        # 数字清洗
        for col in df.columns:
            if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty']):
                try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                except: pass
        return df
    except Exception as e: st.error(f"加载失败: {e}"); return None

def get_dataframe_info(df, name="df"):
    """构建带枚举值的表头信息"""
    if df is None: return f"{name}: 未加载"
    info = [f"### 表名: `{name}` ({len(df)} 行)"]
    info.append("| 列名 | 类型 | 示例值 (Top 20 枚举) |")
    info.append("|---|---|---|")
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        if df[col].dtype == 'object' or 'category' in str(df[col].dtype):
            uniques = df[col].dropna().unique()
            sample = list(uniques[:20]) # 限制枚举数量
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

# ================= 4. 页面渲染 =================

inject_custom_css()
client = get_client()

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

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📂 数据中心")
    st.caption("请上传您的业务数据文件")
    
    up_fact = st.file_uploader("1. 销售事实表 (Fact)", type=["csv", "xlsx"], key="u1")
    up_dim = st.file_uploader("2. 产品维度表 (Dim)", type=["csv", "xlsx"], key="u2")
    
    df_sales = load_data_from_upload(up_fact, "Fact")
    df_product = load_data_from_upload(up_dim, "Dim")
    
    # 诊断信息
    st.divider()
    if df_sales is not None and df_product is not None:
        if JOIN_KEY in df_sales.columns and JOIN_KEY in df_product.columns:
            s_keys = set(df_sales[JOIN_KEY].unique())
            p_keys = set(df_product[JOIN_KEY].unique())
            overlap = s_keys.intersection(p_keys)
            match_rate = len(overlap) / len(s_keys) if len(s_keys) > 0 else 0
            
            if match_rate == 0:
                st.markdown(f"""
                <div class="error-box">
                    ⚠️ 关联键匹配失败 (0%)<br>
                    请检查 `{JOIN_KEY}` 列格式
                </div>
                """, unsafe_allow_html=True)
                with st.expander("查看键值样本"):
                    st.write("Fact:", list(s_keys)[:3])
                    st.write("Dim:", list(p_keys)[:3])
            else:
                st.success(f"🔗 关联正常 (匹配率 {match_rate:.1%})")
        else:
            st.error(f"❌ 缺少核心列 `{JOIN_KEY}`")
    
    if df_sales is not None: st.markdown(f"**Fact表**: `{len(df_sales):,}` 行")
    if df_product is not None: st.markdown(f"**Dim表**: `{len(df_product):,}` 行")

    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Chat History 渲染 ---
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
    st.session_state.messages.append({"role": "user", "type": "text", "content": query})
    st.rerun()

# --- Logic ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        if df_sales is None or df_product is None:
            st.error("请先上传两份数据文件。")
            st.stop()

        context_info = f"""
        {get_dataframe_info(df_sales, "df_sales")}
        {get_dataframe_info(df_product, "df_product")}
        关联键: `{JOIN_KEY}`
        """

        # 1. 意图识别 (MODEL_FAST: Flash 2.0)
        with st.status("🔄 思考中...", expanded=False) as status:
            prompt_router = f"""
            判断用户意图: "{user_query}"
            输出 JSON: {{ "type": "simple/analysis/irrelevant" }}
            """
            resp = safe_generate(client, MODEL_FAST, prompt_router, "application/json")
            intent = clean_json_string(resp.text).get('type', 'simple')
            status.update(label=f"意图: {intent.upper()}", state="complete")

        # 2. 简单查询 (Simple)
        if intent == 'simple':
            # 【重要】取数逻辑调用 MODEL_SMART (1.5 Pro)
            with st.spinner("⚡ 正在生成代码 (Model: 1.5 Pro)..."):
                prompt_code = f"""
                你是一位 Python 专家。
                用户问题: "{user_query}"
                
                【数据上下文 (含枚举)】
                {context_info}
                
                【严格指令】
                1. 如果用户问“有哪些产品”，**不要按名称过滤**，直接返回 `df_product` 的前 20 行（包含通用名、商品名、企业）。
                2. 如果涉及销量，必须使用 `pd.merge` 关联两表。
                3. **容错机制**: 如果关联后结果为空，尝试直接在 `df_product` 中查找并返回基础信息。
                4. 结果赋值给 `result`。
                
                输出 JSON: {{ "summary": {{ "intent": "...", "metrics": "...", "logic": "..." }}, "code": "..." }}
                """
                resp_code = safe_generate(client, MODEL_SMART, prompt_code, "application/json")
                plan = clean_json_string(resp_code.text)
            
            if plan:
                # 渲染摘要盒子
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

                exec_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np, "result": None}
                
                try:
                    exec(plan['code'], exec_ctx)
                    res = exec_ctx.get('result')
                    
                    if res is not None and not res.empty:
                        st.dataframe(format_display_df(res), use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "type": "df", "content": format_display_df(res)})
                    else:
                        st.warning("⚠️ 关联查询结果为空，为您展示产品库中的相关记录：")
                        fallback_code = f"result = df_product[df_product.astype(str).apply(lambda x: x.str.contains('{user_query[:2]}', case=False)).any(axis=1)].head(10)"
                        try:
                            exec(fallback_code, exec_ctx)
                            res_fallback = exec_ctx.get('result')
                            if res_fallback is not None and not res_fallback.empty:
                                st.dataframe(res_fallback)
                                st.session_state.messages.append({"role": "assistant", "type": "df", "content": res_fallback})
                            else:
                                st.error("在产品库中也未找到相关信息。")
                        except:
                            st.error("查询无结果。")
                except Exception as e:
                    st.error(f"代码错误: {e}")

        # 3. 深度分析 (Analysis)
        elif intent == 'analysis':
            # Step 1: 拆解角度 (MODEL_SMART: 1.5 Pro)
            with st.spinner("🧠 专家拆解分析思路 (Model: 1.5 Pro)..."):
                prompt_plan = f"""
                你是一位医药行业高级分析师。
                用户问题: "{user_query}"
                
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
                st.markdown('<div class="step-header">1. 意图深度解析</div>', unsafe_allow_html=True)
                st.markdown(plan_json.get('intent_analysis'))
                
                angles_data = []
                st.markdown('<div class="step-header">2. 多维分析报告</div>', unsafe_allow_html=True)
                
                # Step 2: 循环执行角度
                for angle in plan_json.get('angles', []):
                    with st.container():
                        st.markdown(f"""
                        <div class="tech-card">
                            <div class="angle-title">📐 {angle['title']}</div>
                            <div class="angle-desc">{angle['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        exec_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np, "result": None}
                        try:
                            exec(angle['code'], exec_ctx)
                            res = exec_ctx.get('result')
                            
                            if res is not None and not res.empty:
                                st.dataframe(format_display_df(res), use_container_width=True)
                                
                                # Step 3: 单点洞察 (MODEL_FAST: Flash 2.0)
                                prompt_mini = f"简要解读数据趋势 (50字内):\n{res.to_string()}"
                                resp_mini = safe_generate(client, MODEL_FAST, prompt_mini)
                                explanation = resp_mini.text
                                st.markdown(f'<div class="mini-insight">💡 {explanation}</div>', unsafe_allow_html=True)
                                
                                angles_data.append({
                                    "title": angle['title'], "desc": angle['desc'], 
                                    "data": res, "explanation": explanation
                                })
                            else:
                                st.warning("暂无数据")
                        except Exception as e:
                            st.error(f"计算错误: {e}")

                # Step 4: 全局总结 (MODEL_SMART: 1.5 Pro)
                if angles_data:
                    st.markdown('<div class="step-header">3. 综合业务洞察</div>', unsafe_allow_html=True)
                    with st.spinner("📝 生成最终综述 (Model: 1.5 Pro)..."):
                        findings = "\n".join([f"[{a['title']}]: {a['explanation']}" for a in angles_data])
                        prompt_final = f"""
                        基于各角度发现回答问题: "{user_query}"
                        
                        【各角度发现】
                        {findings}
                        
                        生成一段专业的 Markdown 总结，不包含建议，仅陈述事实。
                        """
                        resp_final = safe_generate(client, MODEL_SMART, prompt_final)
                        insight_text = resp_final.text
                        st.markdown(f'<div class="insight-box">{insight_text}</div>', unsafe_allow_html=True)

        else:
            st.info("请询问与数据相关的问题。")

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

# ================= 1. 基础配置与视觉体系 (VI) =================

st.set_page_config(
    page_title="ChatBI Pro", 
    layout="wide", 
    page_icon="🧬", 
    initial_sidebar_state="expanded"
)

# --- 模型配置 (根据您的要求映射) ---
MODEL_FAST = "gemini-2.0-flash-exp"       # 用于路由、单点洞察 (Flash 2.0)
MODEL_SMART = "gemini-1.5-pro"            # 用于写代码、拆解分析、最终总结 (3 Pro)

# --- 文件配置 ---
FILE_FACT_SALES = "fact.csv"       
FILE_DIM_PRODUCT = "ipmdata.csv"   
LOGO_FILE = "logo.png"
JOIN_KEY = "药品编码"

PREVIEW_ROW_LIMIT = 500
EXPORT_ROW_LIMIT = 5000   

try:
    FIXED_API_KEY = st.secrets["GENAI_API_KEY"]
except:
    FIXED_API_KEY = ""

# --- 样式注入 (完全保留原版 VI) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        /* ================= VI 变量定义 (医药魔方风格) ================= */
        :root {
            --pc-primary-blue: #005ADE; /* 魔方蓝 */
            --pc-dark-blue: #004099;
            --pc-bg-light: #F4F6F9;
            --pc-text-main: #1A2B47;
            --pc-text-sub: #5E6D82;
        }

        .stApp { background-color: var(--pc-bg-light); font-family: 'Inter', "Microsoft YaHei", sans-serif; color: var(--pc-text-main); }

        /* 顶部导航栏 */
        .fixed-header-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 64px;
            background-color: #FFFFFF; box-shadow: 0 2px 12px rgba(0, 90, 222, 0.08);
            z-index: 999999; display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; border-bottom: 1px solid #E6EBF5;
        }
        .nav-left { display: flex; align-items: center; }
        .nav-logo-img { height: 32px; width: auto; margin-right: 12px; }
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
        .summary-title { font-weight: 700; color: var(--pc-text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
        .summary-list li { margin-bottom: 8px; color: var(--pc-text-main); font-size: 14px; }
        .summary-label { font-weight: 600; color: var(--pc-text-sub); margin-right: 8px; }

        .tech-card {
            background-color: white; padding: 24px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 20px;
            border: 1px solid #E6EBF5; transition: all 0.2s ease-in-out;
        }
        .tech-card:hover { transform: translateY(-2px); border-color: #B3C0D1; }
        .angle-title { font-size: 16px; font-weight: 700; color: var(--pc-primary-blue); margin-bottom: 8px; }
        .angle-desc { font-size: 13px; color: var(--pc-text-sub); line-height: 1.5; }

        .mini-insight {
            background-color: #F4F6F9; padding: 12px 16px; border-radius: 6px;
            font-size: 13px; color: var(--pc-text-sub); margin-top: 15px; border-left: 3px solid #909399;
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
        </style>
    """, unsafe_allow_html=True)

# ================= 2. 核心工具函数 =================

@st.cache_resource
def get_client():
    if not FIXED_API_KEY: return None
    try: return genai.Client(api_key=FIXED_API_KEY, http_options={'api_version': 'v1beta'})
    except Exception as e: st.error(f"SDK Error: {e}"); return None

@st.cache_data
def load_dual_data():
    """加载并清洗双表数据"""
    data = {"sales": None, "product": None}
    
    # 1. 销售表
    if os.path.exists(FILE_FACT_SALES):
        try:
            df = pd.read_csv(FILE_FACT_SALES) if FILE_FACT_SALES.endswith('.csv') else pd.read_excel(FILE_FACT_SALES)
            df.columns = df.columns.str.strip()
            if JOIN_KEY in df.columns: df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip()
            for col in df.columns:
                if any(k in str(col) for k in ['额', '量', 'Sales', 'Qty']):
                    try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    except: pass
            data["sales"] = df
        except Exception as e: st.error(f"Fact Error: {e}")

    # 2. 产品表
    if os.path.exists(FILE_DIM_PRODUCT):
        try:
            df = pd.read_csv(FILE_DIM_PRODUCT) if FILE_DIM_PRODUCT.endswith('.csv') else pd.read_excel(FILE_DIM_PRODUCT)
            df.columns = df.columns.str.strip()
            if JOIN_KEY in df.columns: df[JOIN_KEY] = df[JOIN_KEY].astype(str).str.strip()
            df = df.fillna('')
            data["product"] = df
        except Exception as e: st.error(f"Dim Error: {e}")
    return data

def get_dataframe_info_with_enums(df, name="df"):
    """【核心升级】提取表头 + 枚举值 (Top N)，帮助模型理解数据内容"""
    if df is None: return f"{name}: 未加载"
    
    info = [f"### 表名: `{name}` ({len(df)} 行)"]
    info.append("| 列名 | 类型 | 示例值 (枚举 Top 20) |")
    info.append("|---|---|---|")
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        # 仅对文本/分类列提取枚举
        if df[col].dtype == 'object' or 'category' in str(df[col].dtype):
            uniques = df[col].dropna().unique()
            sample = list(uniques[:20]) # 限制枚举数量
            example_str = str(sample)
        else:
            try: example_str = f"{df[col].min()} ~ {df[col].max()}"
            except: example_str = "数值"
        
        # 截断过长字符串
        if len(example_str) > 200: example_str = example_str[:200] + "..."
        info.append(f"| {col} | {dtype} | {example_str} |")
    
    return "\n".join(info)

def clean_json_string(text):
    """清洗 JSON 字符串，处理 Markdown 代码块"""
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

def format_df_for_display(df_raw):
    if not isinstance(df_raw, pd.DataFrame): return df_raw
    df_fmt = df_raw.copy()
    for col in df_fmt.columns:
        if pd.api.types.is_numeric_dtype(df_fmt[col]):
            if any(x in str(col) for x in ['率', '比', 'Ratio', 'Pct']):
                df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "-")
            else:
                df_fmt[col] = df_fmt[col].apply(lambda x: "{:,.2f}".format(x) if pd.notnull(x) else "-")
    return df_fmt

def get_history_context(messages, turn_limit=3):
    if len(messages) <= 1: return "无历史对话。"
    recent_msgs = messages[-turn_limit*2:]
    context = []
    for msg in recent_msgs:
        if msg['type'] == 'text':
            context.append(f"{msg['role']}: {msg['content']}")
        elif msg['type'] == 'report_block':
            s = msg['content'].get('summary', {})
            context.append(f"AI (Action): 执行了意图 {s.get('intent')}，计算了 {s.get('metrics')}")
    return "\n".join(context)

# ================= 3. 页面渲染与导航 =================

inject_custom_css()

# Header
logo_b64 = base64.b64encode(open(LOGO_FILE, "rb").read()).decode() if os.path.exists(LOGO_FILE) else ""
logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="nav-logo-img">' if logo_b64 else ""

st.markdown(f"""
<div class="fixed-header-container">
    <div class="nav-left">{logo_html}</div>
    <div class="nav-center">
        <div class="nav-item">HCM</div> 
        <div class="nav-item active">ChatBI</div>
    </div>
    <div class="nav-right">
        <div class="nav-avatar">PRO</div>
        <button class="nav-exit-btn">退出</button>
    </div>
</div>
""", unsafe_allow_html=True)

# State
if "messages" not in st.session_state: st.session_state.messages = []

# ================= 4. 侧边栏与数据 =================

client = get_client()

# 加载数据
raw_data = load_dual_data()
df_sales = raw_data["sales"]
df_product = raw_data["product"]

# 构建包含枚举值的完整上下文
context_info = ""
if df_sales is not None and df_product is not None:
    context_info = f"""
    {get_dataframe_info_with_enums(df_sales, "df_sales")}
    {get_dataframe_info_with_enums(df_product, "df_product")}
    核心关联键: `{JOIN_KEY}`
    """

with st.sidebar:
    st.markdown("### 🛠️ 控制台")
    st.caption("Core: Flash 2.0 + 3 Pro")
    
    if df_sales is not None:
        st.success(f"📊 Fact表: {len(df_sales):,} 行")
    else:
        st.error("Fact表未加载 (fact.csv)")
        
    if df_product is not None:
        st.success(f"📚 Dim表: {len(df_product):,} 行")
    else:
        st.error("Dim表未加载 (ipmdata.csv)")

    st.divider()
    if st.button("🗑️ 清空会话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ================= 5. 聊天主逻辑 =================

# 渲染历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "report_block":
            content = msg["content"]
            mode = content.get('mode', 'simple')
            
            if mode == 'simple':
                # 渲染简单取数卡片
                s = content['summary']
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
                if 'data' in content:
                    st.dataframe(format_df_for_display(content['data']), use_container_width=True)
            
            elif mode == 'analysis':
                # 渲染深度分析报告
                st.markdown('<div class="step-header">1. 意图深度解析</div>', unsafe_allow_html=True)
                st.markdown(content.get('intent', ''))
                
                st.markdown('<div class="step-header">2. 多维分析报告</div>', unsafe_allow_html=True)
                for angle in content.get('angles_data', []):
                    with st.container():
                        st.markdown(f"""
                        <div class="tech-card">
                            <div class="angle-title">📐 {angle['title']}</div>
                            <div class="angle-desc">{angle['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.dataframe(format_df_for_display(angle['data']), use_container_width=True)
                        st.markdown(f'<div class="mini-insight">💡 {angle["explanation"]}</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="step-header">3. 综合业务洞察</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="insight-box">{content.get("insight", "")}</div>', unsafe_allow_html=True)

# 引导卡片
if not st.session_state.messages:
    st.markdown("### 💡 猜你想问")
    c1, c2, c3 = st.columns(3)
    if c1.button("🗺️ 康缘在各省份的份额?"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "康缘在各省份的份额?"}); st.rerun()
    if c2.button("💊 查一下泰中定的销售额"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "查一下泰中定的销售额"}); st.rerun()
    if c3.button("📊 市场增长趋势分析"): 
        st.session_state.messages.append({"role": "user", "type": "text", "content": "分析一下市场增长趋势"}); st.rerun()

# 输入框
if query := st.chat_input("🔎 请输入问题..."):
    st.session_state.messages.append({"role": "user", "type": "text", "content": query})
    st.rerun()

# 处理逻辑
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        # 0. 检查数据
        if df_sales is None or df_product is None:
            st.error("数据未加载完全，请检查 CSV 文件。")
            st.stop()

        # 1. Router (Flash 2.0)
        with st.status("🔄 正在路由意图...", expanded=False) as status:
            prompt_router = f"""
            你是一个数据分析助手。请判断用户问题的类型。
            用户问题: "{user_query}"
            
            分类标准：
            1. "simple": 明确的取数、排名、聚合查询（如：多少钱，销量，前十名）。
            2. "analysis": 开放式分析、原因探究、多维度对比（如：为什么下降，分析市场格局，发展趋势）。
            3. "irrelevant": 与医药/销售/产品完全无关的闲聊。
            
            输出 JSON: {{ "type": "simple/analysis/irrelevant", "reason": "..." }}
            """
            resp_router = safe_generate(client, MODEL_FAST, prompt_router, "application/json")
            intent_res = clean_json_string(resp_router.text)
            intent_type = intent_res.get('type', 'simple')
            status.update(label=f"✅ 识别为: {intent_type.upper()}", state="complete")

        # ==================== 场景 A: 取数 (Simple) ====================
        if intent_type == 'simple':
            with st.spinner("⚡ 正在生成取数代码 (Model: 3 Pro)..."):
                prompt_simple = f"""
                你是一位 Python 数据专家。
                
                【任务】
                1. 拆解意图: 产品范围、时间范围、颗粒度、指标。
                2. 生成代码: 基于双表 (`df_sales`, `df_product`) 和关联键 `{JOIN_KEY}`。
                
                【上下文 (含枚举值)】
                {context_info}
                
                【用户问题】
                "{user_query}"
                
                【代码约束】
                - 必须使用 `pd.merge(df_sales, df_product, on='{JOIN_KEY}', how='inner')` 进行关联。
                - 结果赋值给 `result` (DataFrame)。
                - 严禁绘图。
                
                输出 JSON: {{ 
                    "summary": {{ "intent": "...", "metrics": "...", "logic": "..." }}, 
                    "code": "..." 
                }}
                """
                resp_simple = safe_generate(client, MODEL_SMART, prompt_simple, "application/json")
                plan = clean_json_string(resp_simple.text)
            
            if plan and plan.get('code'):
                # 渲染取数协议卡片
                s = plan['summary']
                st.markdown(f"""
                <div class="summary-box">
                    <div class="summary-title">⚡ 取数执行协议</div>
                    <ul class="summary-list">
                        <li><span class="summary-label">意图</span> {s.get('intent')}</li>
                        <li><span class="summary-label">指标</span> {s.get('metrics')}</li>
                        <li><span class="summary-label">逻辑</span> {s.get('logic')}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                # 执行代码
                exec_ctx = {"df_sales": df_sales, "df_product": df_product, "pd": pd, "np": np, "result": None}
                try:
                    exec(plan['code'], exec_ctx)
                    res = exec_ctx.get('result')
                    
                    if res is not None and not res.empty:
                        st.dataframe(format_df_for_display(res), use_container_width=True)
                        # 保存历史
                        st.session_state.messages.append({
                            "role": "assistant", "type": "report_block", 
                            "content": {"mode": "simple", "summary": s, "data": res}
                        })
                    else:
                        st.warning("查询结果为空，请检查产品名称是否正确。")
                except Exception as e:
                    st.error(f"代码执行错误: {e}")

        # ==================== 场景 B: 分析 (Analysis) ====================
        elif intent_type == 'analysis':
            # Step 1: 拆解角度 (3 Pro)
            with st.spinner("🧠 专家拆解分析思路 (Model: 3 Pro)..."):
                prompt_plan = f"""
                你是一位医药行业高级分析师。
                用户问题: "{user_query}"
                
                【数据上下文 (含枚举值)】
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
                                st.dataframe(format_df_for_display(res), use_container_width=True)
                                
                                # Step 3: 单点洞察 (Flash 2.0)
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

                # Step 4: 全局总结 (3 Pro)
                if angles_data:
                    st.markdown('<div class="step-header">3. 综合业务洞察</div>', unsafe_allow_html=True)
                    with st.spinner("📝 生成最终综述 (Model: 3 Pro)..."):
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
                        
                        # 保存历史
                        st.session_state.messages.append({
                            "role": "assistant", "type": "report_block",
                            "content": {
                                "mode": "analysis", "intent": plan_json.get('intent_analysis'),
                                "angles_data": angles_data, "insight": insight_text
                            }
                        })

        # ==================== 场景 C: 无关 ====================
        else:
            msg = "抱歉，这个问题似乎与当前的医药销售数据无关。"
            st.info(msg)
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": msg})

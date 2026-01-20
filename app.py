import streamlit as st
import google.generativeai as genai
import json
import os
import base64
import re
from dotenv import load_dotenv

# 1. โหลด API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(layout="wide", page_title="AI BMC & VPC Generator", page_icon="🛠️")

# --- Setup Image ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

logo_path = "static/logo_dsd.png"
img_base64 = get_img_as_base64(logo_path)
logo_src = f"data:image/png;base64,{img_base64}" if img_base64 else "https://via.placeholder.com/150?text=Logo+Missing"

# --- Data ---
EXAMPLES_DATA = {
    "🔌 ช่างแอร์/ไฟฟ้า": { "name": "ร้านช่างแอร์และไฟฟ้าบริการ", "product": "บริการล้างแอร์ ซ่อมแอร์ ติดตั้งระบบไฟ เดินสายไฟ", "customer": "เจ้าของบ้านในหมู่บ้านจัดสรร, หอพัก", "usp": "ช่างมาไว ไม่ทิ้งงาน รับประกันงานซ่อม 30 วัน" },
    "🔨 ช่างรับเหมา": { "name": "ช่างสมชาย รับเหมาต่อเติม", "product": "ต่อเติมครัว โรงจอดรถ ปูกระเบื้อง ซ่อมแซมทั่วไป", "customer": "คนในชุมชนระแวกใกล้เคียง 10 กม., ผู้สูงอายุ", "usp": "เป็นคนในพื้นที่ ไว้ใจได้ ปรึกษาหน้างานฟรี" },
    "🏍️ ซ่อมมอไซค์": { "name": "อู่ช่างบอย มอไซค์ซิ่ง", "product": "ซ่อมมอเตอร์ไซค์ ถ่ายน้ำมันเครื่อง ปะยาง แต่งรถ", "customer": "วินมอเตอร์ไซค์, นักเรียน, คนทำงานโรงงาน", "usp": "เปิดเช้าปิดดึก มีรถกระบะไปรับรถเสียถึงที่" },
    "🥬 ผักไฮโดรฯ": { "name": "กรีนฟาร์ม ไฮโดรโปนิกส์", "product": "ผักสลัด (กรีนโอ๊ค, เรดโอ๊ค) ปลอดสารพิษ สดใหม่", "customer": "คนรักสุขภาพ, ร้านสเต็ก, ร้านสลัดโรล", "usp": "ผักสดตัดใหม่ทุกเช้า ไม่ใช้ยาฆ่าแมลง มี QR ตรวจสอบ" },
    "☕ ร้านกาแฟ": { "name": "กาแฟบ้านทุ่ง", "product": "กาแฟสด เมนูน้ำชง โกโก้ ชาเขียว ขนมปังปิ้ง", "customer": "คนในชุมชน, เกษตรกรพักเที่ยง, ขาจรขับรถผ่าน", "usp": "ราคาเข้าถึงง่าย (25-40 บาท) รสชาติเข้มข้น บรรยากาศกันเอง" }
}
EXAMPLE_OPTIONS = ["✨ เริ่มต้นใหม่"] + list(EXAMPLES_DATA.keys())

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .header-container { background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; display: flex; align-items: center; gap: 20px; }
    .logo-img { width: 80px; height: 80px; object-fit: contain; background-color: white; border-radius: 50%; padding: 5px; border: 3px solid #FFC107; flex-shrink: 0; }
    .header-text { text-align: left; width: 100%; }
    .header-main { font-size: 1.5rem; font-weight: bold; margin: 0; color: #FFF; }
    .header-desc { font-size: 0.9rem; opacity: 0.9; color: #FFD54F; }
    @media only screen and (max-width: 768px) { .header-container { flex-direction: column; text-align: center; } .header-main { font-size: 1.2rem; } }
    .stRadio [role=radiogroup] { gap: 8px; flex-wrap: wrap; justify-content: center; padding-bottom: 10px; }
    .stRadio label[data-baseweb="radio"] { background-color: #fff; border: 1px solid #9c27b0; color: #6a1b9a; padding: 5px 12px; border-radius: 15px; cursor: pointer; transition: all 0.2s; font-size: 0.9rem; margin: 0 !important; }
    .stRadio label[data-baseweb="radio"]:hover { background-color: #f3e5f5; }
    .stRadio label[data-baseweb="radio"][aria-checked="true"] { background-color: #4a148c !important; color: #fff !important; border-color: #4a148c !important; font-weight: bold; }
    .stRadio label[data-baseweb="radio"] > div:first-child { display: none; }
    .box { background-color: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; color: #333; height: auto; min-height: 150px; }
    .box h4 { margin: 0 0 8px 0; color: #4a148c; font-size: 0.95rem; font-weight: bold; border-bottom: 2px solid #f3e5f5; padding-bottom: 5px; min-height: 45px; display: flex; align-items: center; }
    .box p { font-size: 0.85rem; line-height: 1.5; color: #555; margin: 0; }
    .bmc-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 10px; }
    .vpc-container { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; margin-bottom: 20px; }
    @media only screen and (max-width: 768px) { .bmc-grid, .vpc-container { display: flex; flex-direction: column; } }
    .vpc-left { background-color: #e8eaf6; border: 1px dashed #3f51b5; padding: 10px; border-radius: 8px; display: flex; flex-direction: column; gap: 8px;}
    .vpc-right { background-color: #e0f2f1; border: 1px dashed #009688; padding: 10px; border-radius: 8px; display: flex; flex-direction: column; gap: 8px;}
    .vp { background-color: #fffde7; border: 2px solid #FFC107; }
    .co { background-color: #fff5f5; border: 1px dashed #dc3545; }
    .rs { background-color: #f0fff4; border: 1px dashed #28a745; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f3e5f5; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #fff; color: #4a148c; border-top: 3px solid #4a148c; }
    button[kind="primary"] { background-color: #4a148c !important; border: none; color: white !important; width: 100%; padding: 0.6rem; border-radius: 8px; }
    .footer-container { margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div class="header-container">
    <img src="{logo_src}" class="logo-img" alt="DSD Logo">
    <div class="header-text">
        <div style="font-size: 1rem; color: #FFD54F;">กรมพัฒนาฝีมือแรงงาน</div>
        <div class="header-main">สำนักงานพัฒนาฝีมือแรงงานสกลนคร</div>
        <div style="border-bottom: 3px solid #FFC107; width: 50px; margin: 8px 0;"></div>
        <div class="header-desc">ระบบสร้างโมเดลธุรกิจ (BMC) & แผนคุณค่า (VPC) อัตโนมัติ</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- AI Function ---
def generate_bmc_vpc(business, product, customer, strength):
    if not api_key: st.error("ไม่พบ API Key"); return None
    genai.configure(api_key=api_key)
    
    # ✅ ใช้ 2.0-flash-lite (เพราะบัญชีคุณมีตัวนี้ และเป็นตัวแทนของ 1.5-flash)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = f"""
    Act as a Business Consultant. Analyze: "{business}" (Product: "{product}", Target: "{customer}", USP: "{strength}").
    
    Return a valid JSON Object with Thai content.
    Keys:
      "customer_jobs", "pains", "gains",
      "products_services", "pain_relievers", "gain_creators",
      "key_partners", "key_activities", "key_resources", "value_propositions", 
      "customer_relationships", "channels", "customer_segments", "cost_structure", "revenue_streams"
    """
    
    try:
        # 2.0 Flash Lite รองรับ JSON Mode ดีมาก
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        text_response = response.text.strip()
        
        # ล้าง Markdown ออก (เผื่อติดมา)
        if "```json" in text_response: text_response = text_response.replace("```json", "").replace("```", "")
        
        data = json.loads(text_response)
        
        # Clean Data
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, list): v = "\n".join([f"- {str(i)}" for i in v])
            elif isinstance(v, dict): v = "\n".join([f"- {item}" for item in v.values()])
            else: v = str(v)
            cleaned[k] = v.replace("['", "").replace("']", "").replace('["', '').replace('"]', '')
        return cleaned

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด (ลองกดใหม่): {e}")
        return {}

# --- Logic ---
if 'form_data' not in st.session_state: st.session_state['form_data'] = {'name': '', 'product': '', 'customer': '', 'usp': ''}

def update_form():
    sel = st.session_state['radio_select']
    st.session_state['form_data'] = EXAMPLES_DATA.get(sel, {'name': '', 'product': '', 'customer': '', 'usp': ''}).copy()

st.write("##### 💡 เลือกตัวอย่างธุรกิจ:")
current_idx = 0
if st.session_state['form_data']['name']:
    for i, k in enumerate(EXAMPLES_DATA):
        if EXAMPLES_DATA[k]['name'] == st.session_state['form_data']['name']: current_idx = i + 1; break

st.radio("ตัวเลือก", options=EXAMPLE_OPTIONS, index=current_idx, horizontal=True, label_visibility="collapsed", key="radio_select", on_change=update_form)
st.divider()

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. ชื่อธุรกิจ**"); b_name = st.text_input("ชื่อ", st.session_state['form_data']['name'], label_visibility="collapsed")
        st.markdown("**3. ลูกค้า**"); b_cust = st.text_input("ลูกค้า", st.session_state['form_data']['customer'], label_visibility="collapsed")
    with c2:
        st.markdown("**2. สินค้า/บริการ**"); b_prod = st.text_area("สินค้า", st.session_state['form_data']['product'], label_visibility="collapsed", height=104)
        st.markdown("**4. จุดเด่น**"); b_usp = st.text_input("จุดเด่น", st.session_state['form_data']['usp'], label_visibility="collapsed")
    
    submitted = st.form_submit_button("🚀 สร้างแผนธุรกิจ (VPC & BMC)", type="primary")

if submitted:
    if not b_name: st.warning("กรุณากรอกชื่อธุรกิจ")
    else:
        with st.spinner("⏳ AI กำลังวิเคราะห์... (gemini-2.0-flash-lite)"):
            d = generate_bmc_vpc(b_name, b_prod, b_cust, b_usp)
            if d:
                tab1, tab2 = st.tabs(["📋 1. แผนคุณค่า (VPC)", "📊 2. โมเดลธุรกิจ (BMC)"])
                with tab1:
                    vpc_html = f"""
                    <div class="vpc-container">
                        <div class="vpc-left">
                            <div style="text-align:center;color:#3f51b5;font-weight:bold;margin-bottom:10px;">📦 ฝั่งสินค้า (Value Map)</div>
                            <div class="box"><h4>🛍️ Products & Services<br>(สินค้าและบริการ)</h4><p>{d.get('products_services', '-')}</p></div>
                            <div class="box"><h4>💊 Pain Relievers<br>(สิ่งที่ช่วยแก้ปัญหา)</h4><p>{d.get('pain_relievers', '-')}</p></div>
                            <div class="box"><h4>⚡ Gain Creators<br>(สิ่งที่ช่วยสร้างประโยชน์)</h4><p>{d.get('gain_creators', '-')}</p></div>
                        </div>
                        <div class="vpc-right">
                            <div style="text-align:center;color:#00695c;font-weight:bold;margin-bottom:10px;">👤 ฝั่งลูกค้า (Customer Profile)</div>
                            <div class="box"><h4>📝 Customer Jobs<br>(งานที่ลูกค้าต้องทำ)</h4><p>{d.get('customer_jobs', '-')}</p></div>
                            <div class="box"><h4>😫 Pains<br>(ความยุ่งยาก/ปัญหา)</h4><p>{d.get('pains', '-')}</p></div>
                            <div class="box"><h4>😍 Gains<br>(ประโยชน์ที่คาดหวัง)</h4><p>{d.get('gains', '-')}</p></div>
                        </div>
                    </div>
                    """
                    st.markdown(vpc_html, unsafe_allow_html=True)
                with tab2:
                    bmc_html = f"""
                    <div class="bmc-grid">
                        <div class="box kp"><h4>🤝 Key Partners<br>(พันธมิตรหลัก)</h4><p>{d.get('key_partners', '-')}</p></div>
                        <div class="box ka"><h4>⚙️ Key Activities<br>(กิจกรรมหลัก)</h4><p>{d.get('key_activities', '-')}</p></div>
                        <div class="box kr"><h4>🧱 Key Resources<br>(ทรัพยากรหลัก)</h4><p>{d.get('key_resources', '-')}</p></div>
                        <div class="box vp"><h4>🎁 Value Propositions<br>(คุณค่าที่ส่งมอบ)</h4><p>{d.get('value_propositions', '-')}</p></div>
                        <div class="box cr"><h4>❤️ Customer Relationships<br>(ความสัมพันธ์ลูกค้า)</h4><p>{d.get('customer_relationships', '-')}</p></div>
                        <div class="box ch"><h4>🚚 Channels<br>(ช่องทางเข้าถึง)</h4><p>{d.get('channels', '-')}</p></div>
                        <div class="box cs"><h4>👥 Customer Segments<br>(กลุ่มลูกค้าเป้าหมาย)</h4><p>{d.get('customer_segments', '-')}</p></div>
                        <div class="box co"><h4>💰 Cost Structure<br>(โครงสร้างต้นทุน)</h4><p>{d.get('cost_structure', '-')}</p></div>
                        <div class="box rs"><h4>💵 Revenue Streams<br>(กระแสรายได้)</h4><p>{d.get('revenue_streams', '-')}</p></div>
                    </div>
                    """
                    st.markdown(bmc_html, unsafe_allow_html=True)

st.markdown("""<div class="footer-container"><p>© 2025 พัฒนาโดย: <span style="color:#4a148c; font-weight:bold;">สำนักงานพัฒนาฝีมือแรงงานสกลนคร</span> | กรมพัฒนาฝีมือแรงงาน</p></div>""", unsafe_allow_html=True)
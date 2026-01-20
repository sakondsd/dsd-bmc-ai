import streamlit as st
import google.generativeai as genai
import json
import os
import base64
from dotenv import load_dotenv

# 1. โหลด API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    layout="wide", 
    page_title="AI BMC & VPC Generator - DSD Sakon Nakhon",
    page_icon="🛠️"
)

# --- ฟังก์ชันและ Setup รูปภาพ ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

logo_path = "static/logo_dsd.png"
img_base64 = get_img_as_base64(logo_path)
logo_src = f"data:image/png;base64,{img_base64}" if img_base64 else "https://via.placeholder.com/150?text=Logo+Missing"

# --- ข้อมูลตัวอย่าง ---
EXAMPLES_DATA = {
    "🔌 ช่างแอร์/ไฟฟ้า": {
        "name": "ร้านช่างแอร์และไฟฟ้าบริการ",
        "product": "บริการล้างแอร์ ซ่อมแอร์ ติดตั้งระบบไฟ เดินสายไฟ",
        "customer": "เจ้าของบ้านในหมู่บ้านจัดสรร, หอพัก",
        "usp": "ช่างมาไว ไม่ทิ้งงาน รับประกันงานซ่อม 30 วัน"
    },
    "🔨 ช่างรับเหมา": {
        "name": "ช่างสมชาย รับเหมาต่อเติม",
        "product": "ต่อเติมครัว โรงจอดรถ ปูกระเบื้อง ซ่อมแซมทั่วไป",
        "customer": "คนในชุมชนระแวกใกล้เคียง 10 กม., ผู้สูงอายุ",
        "usp": "เป็นคนในพื้นที่ ไว้ใจได้ ปรึกษาหน้างานฟรี"
    },
    "🏍️ ซ่อมมอไซค์": {
        "name": "อู่ช่างบอย มอไซค์ซิ่ง",
        "product": "ซ่อมมอเตอร์ไซค์ ถ่ายน้ำมันเครื่อง ปะยาง แต่งรถ",
        "customer": "วินมอเตอร์ไซค์, นักเรียน, คนทำงานโรงงาน",
        "usp": "เปิดเช้าปิดดึก มีรถกระบะไปรับรถเสียถึงที่"
    },
    "🥬 ผักไฮโดรฯ": {
        "name": "กรีนฟาร์ม ไฮโดรโปนิกส์",
        "product": "ผักสลัด (กรีนโอ๊ค, เรดโอ๊ค) ปลอดสารพิษ สดใหม่",
        "customer": "คนรักสุขภาพ, ร้านสเต็ก, ร้านสลัดโรล",
        "usp": "ผักสดตัดใหม่ทุกเช้า ไม่ใช้ยาฆ่าแมลง มี QR ตรวจสอบ"
    },
    "☕ ร้านกาแฟ": {
        "name": "กาแฟบ้านทุ่ง",
        "product": "กาแฟสด เมนูน้ำชง โกโก้ ชาเขียว ขนมปังปิ้ง",
        "customer": "คนในชุมชน, เกษตรกรพักเที่ยง, ขาจรขับรถผ่าน",
        "usp": "ราคาเข้าถึงง่าย (25-40 บาท) รสชาติเข้มข้น บรรยากาศกันเอง"
    }
}
EXAMPLE_OPTIONS = ["✨ เริ่มต้นใหม่ (ล้างข้อมูล)"] + list(EXAMPLES_DATA.keys())

# --- CSS ตกแต่ง ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Header & Responsive --- */
    .header-container {
        background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%);
        padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15); display: flex; align-items: center; gap: 20px;
    }
    .logo-img { width: 90px; height: 90px; object-fit: contain; background-color: white; border-radius: 50%; padding: 5px; border: 3px solid #FFC107; flex-shrink: 0; }
    .header-text { text-align: left; width: 100%; }
    .header-main { font-size: 1.8rem; font-weight: bold; margin: 0; color: #FFF; line-height: 1.2; }
    .header-sub { font-size: 1.1rem; font-weight: 400; margin-bottom: 5px; color: #FFD54F; }
    .header-line { border-bottom: 3px solid #FFC107; width: 80px; margin: 10px 0; }
    .header-desc { font-size: 1rem; opacity: 0.9; }

    @media only screen and (max-width: 768px) {
        .header-container { flex-direction: column; text-align: center; padding: 15px; gap: 10px; }
        .header-text { text-align: center; } .header-line { margin: 10px auto; }
        .logo-img { width: 70px; height: 70px; }
        .header-main { font-size: 1.4rem; }
    }

    /* --- Radio Button Style --- */
    .stRadio [role=radiogroup] { gap: 10px; flex-wrap: wrap; justify-content: center; padding-bottom: 10px; }
    .stRadio label[data-baseweb="radio"] {
        background-color: #ffffff; border: 2px solid #9c27b0; color: #6a1b9a;
        padding: 8px 16px; border-radius: 20px; cursor: pointer; transition: all 0.2s ease-in-out;
        display: flex; align-items: center; justify-content: center; min-width: 110px; margin: 0 !important;
    }
    .stRadio label[data-baseweb="radio"] > div:first-child { display: none; }
    .stRadio label[data-baseweb="radio"] > div:last-child { padding-left: 0 !important; }
    .stRadio label[data-baseweb="radio"]:hover { background-color: #f3e5f5; border-color: #7b1fa2; transform: translateY(-2px); }
    .stRadio label[data-baseweb="radio"][aria-checked="true"] {
        background-color: #4a148c !important; color: #ffffff !important; border-color: #4a148c !important;
        box-shadow: 0 4px 10px rgba(74, 20, 140, 0.4); transform: translateY(-2px); font-weight: bold;
    }

    /* --- Common Box Style --- */
    .box { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; color: #333; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%; }
    .box h4 { margin-top: 0; color: #4a148c; font-size: 1rem; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #f3e5f5; padding-bottom: 5px; }
    .box p { font-size: 0.9rem; line-height: 1.8; white-space: pre-wrap; color: #555; margin: 0; }

    /* --- BMC Grid --- */
    .bmc-grid { display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(3, minmax(180px, auto)); gap: 12px; margin-top: 20px; margin-bottom: 40px;}
    @media only screen and (max-width: 768px) { .bmc-grid { display: flex; flex-direction: column; } }
    
    .kp { grid-area: 1 / 1 / 3 / 2; background-color: #f3e5f5; } 
    .ka { grid-area: 1 / 2 / 2 / 3; } 
    .kr { grid-area: 2 / 2 / 3 / 3; }
    .vp { grid-area: 1 / 3 / 3 / 4; background-color: #fffde7; border: 2px solid #FFC107; }
    .cr { grid-area: 1 / 4 / 2 / 5; } 
    .ch { grid-area: 2 / 4 / 3 / 5; } 
    .cs { grid-area: 1 / 5 / 3 / 6; background-color: #f3e5f5; }
    .co { grid-area: 3 / 1 / 4 / 3; background-color: #fff5f5; border: 1px dashed #dc3545; }
    .rs { grid-area: 3 / 3 / 4 / 6; background-color: #f0fff4; border: 1px dashed #28a745; }

    /* --- VPC Grid (Value Proposition Canvas) --- */
    .vpc-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
    .vpc-column { display: flex; flex-direction: column; gap: 10px; padding: 15px; border-radius: 10px; }
    
    /* ฝั่งสินค้า (ซ้าย) */
    .vpc-left { background-color: #e8eaf6; border: 2px dashed #3f51b5; }
    .vpc-header-left { color: #304ffe; font-weight: bold; text-align: center; font-size: 1.2rem; margin-bottom: 10px; }
    
    /* ฝั่งลูกค้า (ขวา) */
    .vpc-right { background-color: #e0f2f1; border: 2px dashed #009688; }
    .vpc-header-right { color: #00695c; font-weight: bold; text-align: center; font-size: 1.2rem; margin-bottom: 10px; }

    @media only screen and (max-width: 768px) { .vpc-container { grid-template-columns: 1fr; } }

    /* Button Primary */
    button[kind="primary"] { background-color: #4a148c !important; border: none !important; color: white !important; border-radius: 10px; padding: 0.6rem 1rem; font-size: 1rem; width: 100%; }
    button[kind="primary"]:hover { background-color: #7b1fa2 !important; }
    
    /* Footer */
    .footer-container { margin-top: 50px; padding-top: 20px; border-top: 2px solid #eee; text-align: center; color: #666; font-size: 0.85rem; }
    .footer-credit { font-weight: bold; color: #4a148c; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div class="header-container">
    <img src="{logo_src}" class="logo-img" alt="DSD Logo">
    <div class="header-text">
        <div class="header-sub">กรมพัฒนาฝีมือแรงงาน</div>
        <div class="header-main">สำนักงานพัฒนาฝีมือแรงงานสกลนคร</div>
        <div class="header-line"></div>
        <div class="header-desc">ระบบสร้างโมเดลธุรกิจ (BMC) & แผนคุณค่า (VPC) อัตโนมัติ</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- ฟังก์ชัน AI ---
def generate_bmc_vpc(business, product, customer, strength):
    if not api_key: st.error("ไม่พบ API Key กรุณาตั้งค่าในไฟล์ .env"); return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    บทบาท: คุณคือที่ปรึกษาธุรกิจและผู้เชี่ยวชาญด้าน Design Thinking
    โจทย์: วิเคราะห์ธุรกิจ "{business}" สินค้า "{product}" ลูกค้า "{customer}" จุดเด่น "{strength}"
    
    คำสั่ง 1: สร้าง Business Model Canvas (BMC) 9 ช่อง
    คำสั่ง 2: สร้าง Value Proposition Canvas (VPC) 6 ช่อง
    
    Format: ตอบเป็น JSON Object เท่านั้น keys ตามนี้:
    [BMC]: key_partners, key_activities, key_resources, value_propositions, customer_relationships, channels, customer_segments, cost_structure, revenue_streams
    [VPC - ฝั่งลูกค้า]: customer_jobs (งานที่ลูกค้าต้องทำ), pains (ความยุ่งยาก/ปัญหา), gains (ประโยชน์ที่ลูกค้าคาดหวัง)
    [VPC - ฝั่งสินค้า]: products_services (สินค้าและบริการของเรา), pain_relievers (สิ่งที่ช่วยแก้ปัญหา), gain_creators (สิ่งที่ช่วยสร้างประโยชน์)
    
    Requirement: 
    - ใช้ Bullet point (-) ข้อความสั้นกระชับ ภาษาไทย
    - Cost/Revenue ให้ระบุตัวเลขราคาบาท (ไม่ต้องแยก Fixed/Variable)
    """
    
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        data = json.loads(response.text.strip())
        
        # Data Cleaning
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, dict): value = "\n".join(["\n".join(v) if isinstance(v, list) else str(v) for v in value.values()])
            elif isinstance(value, list): value = "\n".join(map(str, value))
            else: value = str(value)
            cleaned_data[key] = value.replace("['", "").replace("']", "").replace('["', '').replace('"]', '')
        return cleaned_data
    except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}"); return {}

# --- Session State ---
if 'form_data' not in st.session_state:
    st.session_state['form_data'] = {'name': '', 'product': '', 'customer': '', 'usp': ''}

def update_form_from_radio():
    selected = st.session_state['radio_selection']
    if selected in EXAMPLES_DATA: st.session_state['form_data'] = EXAMPLES_DATA[selected].copy()
    else: st.session_state['form_data'] = {'name': '', 'product': '', 'customer': '', 'usp': ''}

# --- UI เลือกตัวอย่าง ---
st.write("##### 💡 เลือกตัวอย่างธุรกิจ (สำหรับทดสอบ):")
current_index = 0
current_name = st.session_state['form_data']['name']
if current_name:
    for i, key in enumerate(EXAMPLES_DATA.keys()):
        if EXAMPLES_DATA[key]['name'] == current_name: current_index = i + 1; break

st.radio("ตัวเลือก", options=EXAMPLE_OPTIONS, index=current_index, label_visibility="collapsed", horizontal=True, key="radio_selection", on_change=update_form_from_radio)

st.divider()

# --- Form รับข้อมูล ---
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. ชื่อธุรกิจ / ประเภท**")
        business_name = st.text_input("ชื่อธุรกิจ", value=st.session_state['form_data']['name'], label_visibility="collapsed")
        st.markdown("**3. ลูกค้าของคุณคือใคร**")
        customer_target = st.text_input("ลูกค้า", value=st.session_state['form_data']['customer'], label_visibility="collapsed")
    with col2:
        st.markdown("**2. สินค้าหรือบริการคืออะไร**")
        product_detail = st.text_area("สินค้า", value=st.session_state['form_data']['product'], label_visibility="collapsed", height=104)
        st.markdown("**4. จุดเด่น / สิ่งที่ลูกค้าชอบ**")
        usp = st.text_input("จุดเด่น", value=st.session_state['form_data']['usp'], label_visibility="collapsed")
    
    submitted = st.form_submit_button("🚀 สร้างแผนธุรกิจ (BMC & VPC)", type="primary")

# --- ผลลัพธ์ ---
if submitted:
    if not business_name:
        st.warning("⚠️ กรุณากรอกชื่อธุรกิจก่อนครับ")
    else:
        with st.spinner("⏳ AI กำลังวิเคราะห์โมเดลธุรกิจและแผนคุณค่า..."):
            data = generate_bmc_vpc(business_name, product_detail, customer_target, usp)
            
            if data:
                st.markdown("### 1. Business Model Canvas (โมเดลธุรกิจ)")
                bmc_html = f"""
                <div class="bmc-grid">
                    <div class="box kp"><h4>🤝 Key Partners<br>(พันธมิตรหลัก)</h4><p>{data.get('key_partners', '-')}</p></div>
                    <div class="box ka"><h4>⚙️ Key Activities<br>(กิจกรรมหลัก)</h4><p>{data.get('key_activities', '-')}</p></div>
                    <div class="box kr"><h4>🧱 Key Resources<br>(ทรัพยากรหลัก)</h4><p>{data.get('key_resources', '-')}</p></div>
                    <div class="box vp"><h4>🎁 Value Propositions<br>(คุณค่าที่ส่งมอบ)</h4><p>{data.get('value_propositions', '-')}</p></div>
                    <div class="box cr"><h4>❤️ Customer Relationships<br>(ความสัมพันธ์ลูกค้า)</h4><p>{data.get('customer_relationships', '-')}</p></div>
                    <div class="box ch"><h4>🚚 Channels<br>(ช่องทางเข้าถึง)</h4><p>{data.get('channels', '-')}</p></div>
                    <div class="box cs"><h4>👥 Customer Segments<br>(กลุ่มลูกค้าเป้าหมาย)</h4><p>{data.get('customer_segments', '-')}</p></div>
                    <div class="box co"><h4>💰 Cost Structure<br>(โครงสร้างต้นทุน)</h4><p>{data.get('cost_structure', '-')}</p></div>
                    <div class="box rs"><h4>💵 Revenue Streams<br>(กระแสรายได้)</h4><p>{data.get('revenue_streams', '-')}</p></div>
                </div>
                """
                st.markdown(bmc_html, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("### 2. Value Proposition Canvas (แผนคุณค่า)")
                st.info("💡 แผนคุณค่าช่วยวิเคราะห์ว่าสินค้าของเรา (ซ้าย) ตอบโจทย์ลูกค้า (ขวา) ได้ตรงจุดหรือไม่")
                
                vpc_html = f"""
                <div class="vpc-container">
                    <div class="vpc-column vpc-left">
                        <div class="vpc-header-left">📦 ฝั่งสินค้า (Value Map)</div>
                        <div class="box" style="background:white;">
                            <h4>🛍️ Products & Services<br>(สินค้าและบริการ)</h4>
                            <p>{data.get('products_services', '-')}</p>
                        </div>
                        <div class="box" style="background:white;">
                            <h4>💊 Pain Relievers<br>(สิ่งที่ช่วยแก้ปัญหา)</h4>
                            <p>{data.get('pain_relievers', '-')}</p>
                        </div>
                        <div class="box" style="background:white;">
                            <h4>⚡ Gain Creators<br>(สิ่งที่ช่วยสร้างประโยชน์)</h4>
                            <p>{data.get('gain_creators', '-')}</p>
                        </div>
                    </div>

                    <div class="vpc-column vpc-right">
                        <div class="vpc-header-right">👤 ฝั่งลูกค้า (Customer Profile)</div>
                         <div class="box" style="background:white;">
                            <h4>📝 Customer Jobs<br>(งานที่ลูกค้าต้องทำ)</h4>
                            <p>{data.get('customer_jobs', '-')}</p>
                        </div>
                        <div class="box" style="background:white;">
                            <h4>😫 Pains<br>(ความยุ่งยาก/ปัญหา)</h4>
                            <p>{data.get('pains', '-')}</p>
                        </div>
                        <div class="box" style="background:white;">
                            <h4>😍 Gains<br>(ประโยชน์ที่คาดหวัง)</h4>
                            <p>{data.get('gains', '-')}</p>
                        </div>
                    </div>
                </div>
                """
                st.markdown(vpc_html, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="footer-container">
    <p>© 2025 พัฒนาโดย: <span class="footer-credit">สำนักงานพัฒนาฝีมือแรงงานสกลนคร</span> | กรมพัฒนาฝีมือแรงงาน</p>
    <p style="font-size: 0.75rem;">เครื่องมือนี้ใช้ AI วิเคราะห์เบื้องต้น ผู้ประกอบการควรพิจารณาความเหมาะสมกับสถานการณ์จริง</p>
</div>
""", unsafe_allow_html=True)
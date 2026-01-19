import streamlit as st
import google.generativeai as genai
import json
import os
import base64
from dotenv import load_dotenv

# 1. โหลด API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ตั้งค่าหน้าเว็บ (Page Config)
st.set_page_config(
    layout="wide", 
    page_title="AI BMC Generator - DSD Sakon Nakhon",
    page_icon="🛠️"
)

# --- ฟังก์ชันแปลงรูปภาพเป็น Base64 ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# โหลดรูปโลโก้
logo_path = "static/logo_dsd.png"
img_base64 = get_img_as_base64(logo_path)

if img_base64:
    logo_src = f"data:image/png;base64,{img_base64}"
else:
    logo_src = "https://via.placeholder.com/150?text=Logo+Missing"

# --- CSS ตกแต่ง (Responsive & Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
    }

    /* --- Header Style (Desktop) --- */
    .header-container {
        background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .logo-img {
        width: 90px;
        height: 90px;
        object-fit: contain;
        background-color: white;
        border-radius: 50%;
        padding: 5px;
        border: 3px solid #FFC107;
        flex-shrink: 0;
    }

    .header-text { text-align: left; width: 100%; }
    .header-main { font-size: 1.8rem; font-weight: bold; margin: 0; color: #FFF; line-height: 1.2; }
    .header-sub { font-size: 1.1rem; font-weight: 400; margin-bottom: 5px; color: #FFD54F; }
    .header-line { border-bottom: 3px solid #FFC107; width: 80px; margin: 10px 0; }
    .header-desc { font-size: 1rem; opacity: 0.9; }

    /* --- 📱 Mobile Optimization (Media Query) --- */
    @media only screen and (max-width: 768px) {
        .header-container {
            flex-direction: column;
            text-align: center;
            padding: 15px;
            gap: 10px;
        }
        .header-text { text-align: center; }
        .header-line { margin: 10px auto; }
        
        .logo-img { width: 70px; height: 70px; }
        .header-main { font-size: 1.4rem; }
        .header-sub { font-size: 0.9rem; }
        .header-desc { font-size: 0.8rem; }
        
        div[data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: 0px !important; }
    }

    /* --- BMC Grid Layout --- */
    .bmc-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        grid-template-rows: repeat(3, minmax(180px, auto));
        gap: 12px;
        margin-top: 20px;
    }
    @media only screen and (max-width: 768px) {
        .bmc-grid { display: flex; flex-direction: column; }
    }

    .box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        color: #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .box h4 { margin-top: 0; color: #4a148c; font-size: 0.95rem; font-weight: bold; margin-bottom: 10px; }
    .box p { font-size: 0.9rem; line-height: 1.8; white-space: pre-wrap; color: #555; margin: 0; }
    
    /* Mapping & Colors */
    .kp { grid-area: 1 / 1 / 3 / 2; background-color: #f3e5f5; }
    .ka { grid-area: 1 / 2 / 2 / 3; }
    .kr { grid-area: 2 / 2 / 3 / 3; }
    .vp { grid-area: 1 / 3 / 3 / 4; background-color: #fffde7; border: 2px solid #FFC107; } 
    .cr { grid-area: 1 / 4 / 2 / 5; }
    .ch { grid-area: 2 / 4 / 3 / 5; }
    .cs { grid-area: 1 / 5 / 3 / 6; background-color: #f3e5f5; }
    .co { grid-area: 3 / 1 / 4 / 3; background-color: #fff5f5; border: 1px dashed #dc3545; } 
    .rs { grid-area: 3 / 3 / 4 / 6; background-color: #f0fff4; border: 1px dashed #28a745; }

    /* Button Style */
    .stButton button { 
        width: 100%; border-radius: 10px; font-size: 0.85rem; height: auto; padding: 0.5rem 0.2rem;
        border: 1px solid #7b1fa2; color: #4a148c; background-color: #f3e5f5;
    }
    .stButton button:hover { background-color: #e1bee7; border-color: #4a148c; }
    button[kind="primary"] { background-color: #4a148c !important; border: none !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #7b1fa2 !important; }

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
        <div class="header-desc">ระบบสร้างโมเดลธุรกิจอัตโนมัติ (AI Business Model Canvas)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. ฟังก์ชันเรียก AI (ใช้ JSON Mode)
def generate_bmc(business, product, customer, strength):
    if not api_key:
        st.error("ไม่พบ API Key กรุณาตั้งค่าในไฟล์ .env")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    บทบาท: คุณคือที่ปรึกษาธุรกิจและนักบัญชีมืออาชีพ
    
    โจทย์: สร้าง Business Model Canvas สำหรับ
    - ธุรกิจ: "{business}"
    - สินค้า: "{product}"
    - ลูกค้า: "{customer}"
    - จุดเด่น: "{strength}"

    **คำสั่งสำคัญ:**
    1. ตอบเป็น JSON Object เท่านั้น (ไม่ต้องมี Markdown ```json)
    2. ใช้ Bullet point (-) สำหรับข้อย่อย
    3. ช่อง Cost Structure และ Revenue Streams ให้รวมรายการมาเลย ไม่ต้องแยก Fixed/Variable ให้ระบุตัวเลขราคา/บาท ให้ชัดเจน

    Output Keys:
    key_partners, key_activities, key_resources, value_propositions, customer_relationships, 
    channels, customer_segments, cost_structure, revenue_streams
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        text_response = response.text.strip()
        data = json.loads(text_response)
        
        # Data Flattening
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                items = []
                for k, v in value.items():
                    if isinstance(v, list):
                        items.extend(v)
                    else:
                        items.append(str(v))
                value = "\n".join(items)
            elif isinstance(value, list):
                value = "\n".join(map(str, value))
            else:
                value = str(value)
            
            cleaned_data[key] = value.replace("['", "").replace("']", "").replace('["', '').replace('"]', '')
            
        return cleaned_data

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
        return {}

# --- Session State ---
if 'form_data' not in st.session_state:
    st.session_state['form_data'] = {'name': '', 'product': '', 'customer': '', 'usp': ''}

def set_example(name, product, customer, usp):
    st.session_state['form_data'] = {'name': name, 'product': product, 'customer': customer, 'usp': usp}

# UI เลือกตัวอย่าง
st.markdown("##### 💡 เลือกตัวอย่างธุรกิจ:")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔌 ช่างแอร์/ไฟฟ้า"): set_example("ร้านช่างแอร์และไฟฟ้าบริการ", "บริการล้างแอร์ ซ่อมแอร์ ติดตั้งระบบไฟ", "เจ้าของบ้านในหมู่บ้านจัดสรร", "ช่างมาไว รับประกันงานซ่อม 30 วัน")
with c2:
    if st.button("🔨 ช่างรับเหมา"): set_example("ช่างสมชาย รับเหมาต่อเติม", "ต่อเติมครัว โรงจอดรถ ปูกระเบื้อง", "คนในชุมชนระแวกใกล้เคียง", "คนพื้นที่ ไว้ใจได้")
with c3:
    if st.button("🏍️ ซ่อมมอไซค์"): set_example("อู่ช่างบอย มอไซค์ซิ่ง", "ซ่อมมอเตอร์ไซค์ ถ่ายน้ำมันเครื่อง ปะยาง", "วินมอเตอร์ไซค์, นักเรียน", "เปิดเช้าปิดดึก มีรถรับส่ง")
with c4:
    if st.button("🥬 ผักไฮโดรฯ"): set_example("กรีนฟาร์ม ไฮโดรโปนิกส์", "ผักสลัดปลอดสารพิษ", "คนรักสุขภาพ, ร้านสเต็ก", "ตัดใหม่ทุกเช้า ไม่ใช้ยาฆ่าแมลง")
with c5:
    if st.button("☕ ร้านกาแฟ"): set_example("กาแฟบ้านทุ่ง", "กาแฟสด เมนูน้ำชง", "คนในชุมชน, ขาจร", "ราคาเข้าถึงง่าย (25-40 บาท)")

st.divider()

# Form
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
    
    submitted = st.form_submit_button("🚀 สร้างแผนธุรกิจ (BMC)", type="primary")

# Result
if submitted:
    if not business_name:
        st.warning("⚠️ กรุณากรอกชื่อธุรกิจก่อนครับ")
    else:
        with st.spinner("⏳ AI กำลังวิเคราะห์ข้อมูล..."):
            data = generate_bmc(business_name, product_detail, customer_target, usp)
            
            if data:
                # แสดงผลตาราง 9 ช่อง พร้อมหัวข้อภาษาไทย
                html_code = f"""
                <div class="bmc-grid">
                    <div class="box kp"><h4>🤝 พันธมิตรหลัก (Key Partners)</h4><p>{data.get('key_partners', '-')}</p></div>
                    <div class="box ka"><h4>⚙️ กิจกรรมหลัก (Key Activities)</h4><p>{data.get('key_activities', '-')}</p></div>
                    <div class="box kr"><h4>🧱 ทรัพยากรหลัก (Key Resources)</h4><p>{data.get('key_resources', '-')}</p></div>
                    <div class="box vp"><h4>🎁 คุณค่าหลัก (Value Propositions)</h4><p>{data.get('value_propositions', '-')}</p></div>
                    <div class="box cr"><h4>❤️ ความสัมพันธ์ลูกค้า (Relationships)</h4><p>{data.get('customer_relationships', '-')}</p></div>
                    <div class="box ch"><h4>🚚 ช่องทางเข้าถึง (Channels)</h4><p>{data.get('channels', '-')}</p></div>
                    <div class="box cs"><h4>👥 กลุ่มลูกค้า (Customer Segments)</h4><p>{data.get('customer_segments', '-')}</p></div>
                    <div class="box co"><h4>💰 โครงสร้างต้นทุน (Cost Structure)</h4><p>{data.get('cost_structure', '-')}</p></div>
                    <div class="box rs"><h4>💵 กระแสรายได้ (Revenue Streams)</h4><p>{data.get('revenue_streams', '-')}</p></div>
                </div>
                """
                st.markdown(html_code, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer-container">
    <p>© 2025 พัฒนาโดย: <span class="footer-credit">สำนักงานพัฒนาฝีมือแรงงานสกลนคร</span> | กรมพัฒนาฝีมือแรงงาน</p>
    <p style="font-size: 0.75rem;">เครื่องมือนี้ใช้ AI วิเคราะห์เบื้องต้น ผู้ประกอบการควรพิจารณาความเหมาะสมกับสถานการณ์จริง</p>
</div>
""", unsafe_allow_html=True)
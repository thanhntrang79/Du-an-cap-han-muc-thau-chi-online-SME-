import streamlit as st
import pandas as pd
from fpdf import FPDF # Thư viện để tạo PDF

# 1. Cấu hình giao diện
st.set_page_config(page_title="Eximbank AI Lending", layout="wide")

# Hiển thị Logo
st.image("logo.jpg", width=150)

st.title("🏦 Hệ Thống Thẩm Định Đề Xuất Cấp Hạn Mức Thấu Chi Online")
st.markdown("---")

# 2. Thanh điều hướng bên trái
with st.sidebar:
    st.header("📋 1. Định danh & CIC")
    customer_name = st.text_input("Tên khách hàng", "Nguyễn Văn A")
    customer_cic = st.number_input("Nhập điểm CIC khách hàng", min_value=0, max_value=850, value=650)
    
    st.write("---")
    st.header("🏠 2. Tài sản đảm bảo")
    asset_value = st.number_input("Tổng giá trị tài sản (VND)", min_value=0, value=1000000000, step=10000000)
    loan_amount_existing = st.number_input("Số tiền đã vay nơi khác (VND)", min_value=0, value=200000000, step=10000000)
    
    remaining_asset_value = asset_value - loan_amount_existing
    limit_by_asset = remaining_asset_value * 0.1 if remaining_asset_value > 0 else 0
    
    st.write("---")
    uploaded_file = st.file_uploader("Upload sao kê giao dịch (.xlsx)", type=["xlsx"])

# 3. Logic xử lý và Xuất PDF
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        # (Phần xử lý dòng tiền giữ nguyên như cũ của chị)
        tong_thu = 500000000 # Giả lập số liệu để chị thấy nút PDF
        dong_tien_thuan = 300000000
        
        # Giả sử tính ra hạn mức cuối cùng
        final_limit = min(dong_tien_thuan * 3, limit_by_asset)

        st.metric("Hạn mức phê duyệt cuối cùng", f"{final_limit:,.0f} VND")

        # NÚT XUẤT PDF
        if final_limit > 0:
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 15)
                    self.cell(0, 10, 'BAO CAO THAM DINH THAU CHI ONLINE - EXIMBANK', 0, 1, 'C')

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Khach hang: {customer_name}", ln=1, align='L')
            pdf.cell(200, 10, txt=f"Diem CIC: {customer_cic}", ln=2, align='L')
            pdf.cell(200, 10, txt=f"Gia tri TSDB: {asset_value:,.0f} VND", ln=3, align='L')
            pdf.cell(200, 10, txt=f"Han muc phe duyet: {final_limit:,.0f} VND", ln=4, align='L')
            pdf.cell(200, 10, txt=f"Trang thai: DU DIEU KIEN", ln=5, align='L')

            pdf_output = pdf.output(dest='S').encode('latin-1')
            
            st.download_button(
                label="📥 Tải báo cáo phê duyệt (PDF)",
                data=pdf_output,
                file_name=f"Bao_cao_phe_duyet_{customer_name}.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Lỗi: {e}")

import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64

# 1. Cấu hình giao diện
st.set_page_config(page_title="Eximbank AI Lending", layout="wide")

# Hiển thị Logo trên trang Web
st.image("logo.jpg", width=200)

st.title("🏦 Hệ Thống Thẩm Định Đề Xuất Cấp Hạn Mức Thấu Chi Online")
st.markdown("---")

# 2. Thanh điều hướng bên trái (Sidebar)
with st.sidebar:
    st.header("📋 1. Định danh & CIC")
    customer_cic = st.number_input("Nhập điểm CIC khách hàng", min_value=0, max_value=850, value=650)
    
    st.write("---")
    st.header("🏠 2. Tài sản đảm bảo (TSĐB)")
    asset_value = st.number_input("Tổng giá trị tài sản (VND)", min_value=0, value=1000000000, step=10000000)
    st.caption(f"Giá trị: **{asset_value:,.0f}** VND")
    
    loan_amount_existing = st.number_input("Số tiền đã được cấp tín dụng (VND)", min_value=0, value=200000000, step=10000000)
    st.caption(f"Đã vay: **{loan_amount_existing:,.0f}** VND")
    
    remaining_asset_value = asset_value - loan_amount_existing
    limit_by_asset = remaining_asset_value * 0.1 if remaining_asset_value > 0 else 0
    
    st.write("---")
    st.write(f"✅ **Giá trị TS còn lại:** {remaining_asset_value:,.0f} VND")
    st.write(f"✅ **Hạn mức còn lại(10%):** {limit_by_asset:,.0f} VND")
    
    st.write("---")
    st.header("📊 3. Dữ liệu dòng tiền")
    uploaded_file = st.file_uploader("Upload sao kê giao dịch (.xlsx)", type=["xlsx"])

# 3. Xử lý logic chính
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        def classify_transaction(text):
            text = str(text).upper()
            if any(k in text for k in ['QR', 'THANH TOAN DEN', 'CHUYEN DEN', 'DOANH THU']):
                return 'DOANH THU'
            elif any(k in text for k in ['LUONG', 'DIEN', 'NUOC', 'THUE', 'NHAP HANG', 'INTERNET']):
                return 'CHI PHI'
            return 'KHAC'

        if 'Noi_Dung' in df.columns and 'So_Tien' in df.columns:
            df['Phan_Loai'] = df['Noi_Dung'].apply(classify_transaction)
            tong_thu = df[df['Phan_Loai'] == 'DOANH THU']['So_Tien'].sum()
            tong_chi = abs(df[df['Phan_Loai'] == 'CHI PHI']['So_Tien'].sum())
            dong_tien_thuan = tong_thu - tong_chi

            # Hiển thị chỉ số
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dòng tiền thuần", f"{dong_tien_thuan:,.0f} VND")
            c2.metric("Điểm CIC", f"{customer_cic}")
            c3.metric("Giá trị TS còn lại", f"{remaining_asset_value:,.0f} VND")
            c4.metric("hạn mức TS còn lại (10%)", f"{limit_by_asset:,.0f} VND")

            st.markdown("---")
            st.subheader("🎯 Kết quả phê duyệt cuối cùng từ Eximbank:")

            if dong_tien_thuan > 0:
                base_limit = min(dong_tien_thuan * 3, 500000000)
                if customer_cic < 300: rate, status = 0.0, "Tu choi"
                elif 300 <= customer_cic < 400: rate, status = 0.3, "Duyet 30%"
                elif 400 <= customer_cic < 500: rate, status = 0.5, "Duyet 50%"
                elif 500 <= customer_cic < 600: rate, status = 0.8, "Duyet 80%"
                else: rate, status = 1.0, "Duyet 100%"
                
                limit_by_cashflow = base_limit * rate
                final_limit = min(limit_by_cashflow, limit_by_asset)

                if final_limit > 0:
                    st.success(f"✅ HỒ SƠ ĐỦ ĐIỀU KIỆN VAY")
                    st.markdown(f"### **Hạn mức phê duyệt cuối cùng: <span style='color:red;'>{final_limit:,.0f} VND</span>**", unsafe_allow_html=True)
                    
                    # --- PHẦN TẠO PDF ---
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(200, 10, txt="BAO CAO THAM DINH TIN DUNG ONLINE", ln=True, align='C')
                    pdf.set_font("Arial", size=12)
                    pdf.ln(10)
                    pdf.cell(200, 10, txt=f"Khach hang: {customer_name}", ln=True)
                    pdf.cell(200, 10, txt=f"Diem CIC: {customer_cic}", ln=True)
                    pdf.cell(200, 10, txt=f"Han muc de xuat: {final_limit:,.0f} VND", ln=True)
                    pdf.cell(200, 10, txt=f"Trang thai: {status}", ln=True)
                    pdf.ln(10)
                    pdf.cell(200, 10, txt="Xac nhan boi: He thong Eximbank", ln=True)
                    
                    # Xuất file PDF
                    pdf_data = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="📥 Tải Báo Cáo Phê Duyệt (PDF)",
                        data=pdf_data,
                        file_name=f"Bao_cao_phe_duyet_{customer_name}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ TỪ CHỐI. Hạn mức bằng 0.")
            else:
                st.error("❌ TỪ CHỐI. Dòng tiền âm.")

            st.write("### 📑 Chi tiết giao dịch")
            st.dataframe(df.style.format({"So_Tien": "{:,.0f}"}), use_container_width=True)
            
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")

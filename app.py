import streamlit as st
from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt

from sam_model import load_sam_model, get_rooftop_mask
from utils import calculate_area_from_mask, estimate_solar_metrics
from report_generator import generate_pdf_report

st.set_page_config(page_title="Solar AI Assistant", layout="wide")

st.title("☀️ SolarAIAssistant – AI + pvlib Rooftop Analysis")

# ---------------------------
# Sidebar Controls
# ---------------------------
st.sidebar.header("🌍 Location & System Settings")

latitude = st.sidebar.number_input("Latitude", value=28.6139)
longitude = st.sidebar.number_input("Longitude", value=77.2090)

tilt = st.sidebar.slider("Panel Tilt (°)", 0, 45, 20)
azimuth = st.sidebar.slider("Azimuth (°)", 0, 360, 180)

optimize = st.sidebar.checkbox("🔬 Auto Optimize Tilt")

uploaded_file = st.file_uploader("📤 Upload Rooftop Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("🤖 Detecting rooftop using SAM..."):
        sam = load_sam_model()
        mask = get_rooftop_mask(image, sam)

    if mask is not None:
        st.success("Rooftop detected!")

        masked_image_np = np.array(image)
        masked_image_np[~mask] = [0, 0, 0]
        st.image(masked_image_np, caption="Detected Rooftop", use_container_width=True)

        area_m2 = calculate_area_from_mask(mask)

        metrics, monthly_generation = estimate_solar_metrics(
            area_m2,
            latitude,
            longitude,
            tilt,
            azimuth,
            optimize
        )

        st.subheader("📊 Solar Metrics")
        st.write(f"**Usable Rooftop Area:** {area_m2} m²")
        st.write(f"**System Size:** {metrics['system_size_kw']} kW")
        st.write(f"**Annual Generation:** {metrics['annual_generation_kwh']} kWh")
        st.write(f"**Optimal Tilt Used:** {metrics['tilt_used']}°")
        st.write(f"**Specific Yield:** {metrics['specific_yield']} kWh/kWp")
        st.write(f"**CO₂ Offset:** {metrics['co2_offset_tons']} tons/year")
        st.write(f"**Payback Period:** {metrics['payback_years']} years")
        st.write(f"**ROI:** {metrics['roi_percent']}%")

        # Monthly plot
        st.subheader("📈 Monthly Energy Output")
        fig, ax = plt.subplots()
        ax.plot(monthly_generation.index, monthly_generation.values)
        ax.set_ylabel("kWh")
        ax.set_xlabel("Month")
        st.pyplot(fig)

        if st.button("📄 Generate PDF Report"):
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)

            image_path = os.path.join(output_dir, "masked_image.jpg")
            report_path = os.path.join(output_dir, "solar_ai_report.pdf")

            Image.fromarray(masked_image_np).save(image_path)
            generate_pdf_report(report_path, image_path, area_m2, metrics)

            with open(report_path, "rb") as f:
                st.download_button("📥 Download Report", f, file_name="solar_ai_report.pdf")

    else:
        st.error("No rooftop detected. Upload a clearer image.")

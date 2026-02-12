import streamlit as st
from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt

from sam_model import load_sam_model, get_rooftop_mask
from utils import calculate_area_from_mask, estimate_solar_metrics


st.set_page_config(page_title="SolarAIAssistant", layout="wide")

st.title("SolarAIAssistant")
st.subheader("Rooftop Solar Feasibility and Savings Estimator for Indian Households")

st.markdown(
    """
    This application helps evaluate rooftop solar feasibility under the 
    PM Surya Ghar Yojana using physics-based simulation and financial modeling.
    """
)

# -------------------------------------------------------
# Input Method Selection
# -------------------------------------------------------

st.header("Input Method")

input_mode = st.radio(
    "Select how you would like to evaluate your solar installation:",
    ["Monthly Electricity Bill", "Rooftop Image (AI Detection)"]
)

# -------------------------------------------------------
# Location Settings
# -------------------------------------------------------

st.header("Location Settings")

latitude = st.number_input("Latitude", value=28.6139, format="%.6f")
longitude = st.number_input("Longitude", value=77.2090, format="%.6f")

tilt = st.slider("Panel Tilt (degrees)", 0, 45, 20)
azimuth = st.slider("Panel Azimuth (degrees)", 0, 360, 180)

optimize = st.checkbox("Automatically optimize tilt")

# -------------------------------------------------------
# Bill-Based Mode
# -------------------------------------------------------

if input_mode == "Monthly Electricity Bill":

    st.header("Electricity Bill Details")

    monthly_bill = st.number_input("Monthly Electricity Bill (₹)", min_value=0.0)

    state_tariff = st.number_input(
        "Electricity Tariff (₹ per kWh)",
        min_value=0.0,
        value=8.0
    )

    if st.button("Run Feasibility Analysis"):

        if monthly_bill <= 0:
            st.error("Please enter a valid monthly electricity bill.")
        else:
            annual_bill = monthly_bill * 12
            annual_consumption = annual_bill / state_tariff

            # Assume 1 kW produces approx 1400 kWh/year (rough Indian avg)
            estimated_system_size = annual_consumption / 1400

            metrics, monthly_generation = estimate_solar_metrics(
                area_m2=estimated_system_size / 0.18,
                latitude=latitude,
                longitude=longitude,
                tilt=tilt,
                azimuth=azimuth,
                optimize=optimize
            )

            st.header("Solar System Results")

            st.write(f"Estimated System Size: {metrics['system_size_kw']} kW")
            st.write(f"Estimated Annual Generation: {metrics['annual_generation_kwh']} kWh")
            st.write(f"Performance Ratio: {metrics['performance_ratio']}")
            st.write(f"Payback Period: {metrics['payback_years']} years")
            st.write(f"Return on Investment: {metrics['roi_percent']} %")

            # Plot monthly generation
            fig, ax = plt.subplots()
            ax.plot(monthly_generation.index, monthly_generation.values)
            ax.set_ylabel("Energy (kWh)")
            ax.set_xlabel("Month")
            st.pyplot(fig)


# -------------------------------------------------------
# Rooftop Image Mode
# -------------------------------------------------------

elif input_mode == "Rooftop Image (AI Detection)":

    st.header("Upload Rooftop Image")

    uploaded_file = st.file_uploader(
        "Upload a satellite or aerial image of your rooftop",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:

        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Image", use_container_width=True)

        with st.spinner("Detecting rooftop area..."):
            sam = load_sam_model()
            mask = get_rooftop_mask(image, sam)

        if mask is None:
            st.error("Rooftop could not be detected. Please upload a clearer image.")
        else:
            masked_image_np = np.array(image)
            masked_image_np[~mask] = [0, 0, 0]

            st.image(
                masked_image_np,
                caption="Detected Rooftop Area",
                use_container_width=True
            )

            area_m2 = calculate_area_from_mask(mask)

            metrics, monthly_generation = estimate_solar_metrics(
                area_m2=area_m2,
                latitude=latitude,
                longitude=longitude,
                tilt=tilt,
                azimuth=azimuth,
                optimize=optimize
            )

            st.header("Solar System Results")

            st.write(f"Usable Rooftop Area: {area_m2} m²")
            st.write(f"System Size: {metrics['system_size_kw']} kW")
            st.write(f"Annual Generation: {metrics['annual_generation_kwh']} kWh")
            st.write(f"Performance Ratio: {metrics['performance_ratio']}")
            st.write(f"Payback Period: {metrics['payback_years']} years")
            st.write(f"Return on Investment: {metrics['roi_percent']} %")

            fig, ax = plt.subplots()
            ax.plot(monthly_generation.index, monthly_generation.values)
            ax.set_ylabel("Energy (kWh)")
            ax.set_xlabel("Month")
            st.pyplot(fig)

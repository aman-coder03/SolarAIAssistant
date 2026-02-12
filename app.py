import streamlit as st
from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt

from sam_model import load_sam_model, get_rooftop_mask
from utils import calculate_area_from_mask, estimate_solar_metrics

@st.cache_resource
def load_cached_sam():
    return load_sam_model()

def display_results(metrics, monthly_generation):

    st.header("Solar System Results")

    st.write(f"System Size: {metrics['system_size_kw']} kW")
    st.write(f"Annual Generation: {metrics['annual_generation_kwh']} kWh")
    st.write(f"Performance Ratio: {metrics['performance_ratio']}")
    st.write(f"Installation Cost: ₹{metrics['installation_cost']}")
    st.write(f"Subsidy (PM Surya Ghar): ₹{metrics['subsidy']}")
    st.write(f"Net Cost After Subsidy: ₹{metrics['net_cost']}")
    st.write(f"Estimated Annual Savings: ₹{metrics['annual_savings']}")
    st.write(f"Estimated Payback Period: {metrics['payback_years']} years")
    st.write(f"Return on Investment: {metrics['roi_percent']} %")

    # Monthly generation plot
    st.subheader("Monthly Energy Output")
    fig, ax = plt.subplots()
    ax.plot(monthly_generation.index, monthly_generation.values)
    ax.set_ylabel("Energy (kWh)")
    ax.set_xlabel("Month")
    st.pyplot(fig)

    # 10-Year Projection Plot
    st.subheader("10-Year Savings Projection")

    fig2, ax2 = plt.subplots()
    ax2.plot(range(1, 11), metrics["cumulative_savings"])
    ax2.set_ylabel("Cumulative Savings (₹)")
    ax2.set_xlabel("Year")
    st.pyplot(fig2)

    # Final recommendation logic
    if metrics["payback_years"] <= 6:
        st.success("Recommendation: Rooftop solar installation appears financially attractive.")
    elif metrics["payback_years"] <= 10:
        st.warning("Recommendation: Rooftop solar may be viable with moderate financial return.")
    else:
        st.error("Recommendation: Financial return may be slow under current assumptions.")

st.set_page_config(page_title="SolarAIAssistant", layout="wide")

st.title("SolarAIAssistant")
st.subheader("Rooftop Solar Feasibility and Savings Estimator for Indian Households")

st.markdown(
    """
    Evaluate rooftop solar installation under PM Surya Ghar Yojana
    using physics-based energy simulation and financial modeling.
    """
)

# Input Method Selection

st.header("Input Method")

input_mode = st.radio(
    "Select evaluation method:",
    ["Monthly Electricity Bill", "Rooftop Image (AI Detection)"]
)

# Location Settings

st.header("Location Settings")

latitude = st.number_input("Latitude", value=28.6139, format="%.6f")
longitude = st.number_input("Longitude", value=77.2090, format="%.6f")

tilt = st.slider("Panel Tilt (degrees)", 0, 45, 20)
azimuth = st.slider("Panel Azimuth (degrees)", 0, 360, 180)

optimize = st.checkbox("Automatically optimize tilt")

tariff = st.number_input(
    "Electricity Tariff (₹ per kWh)",
    min_value=0.1,
    value=8.0
)

if tariff <= 0:
    st.error("Electricity tariff must be greater than zero.")
    st.stop()

# BILL MODE

if input_mode == "Monthly Electricity Bill":

    st.header("Electricity Bill Details")

    monthly_bill = st.number_input("Monthly Electricity Bill (₹)", min_value=0.0)

    if st.button("Run Feasibility Analysis"):

        if monthly_bill <= 0:
            st.error("Please enter a valid monthly electricity bill.")
        else:
            annual_bill = monthly_bill * 12
            annual_consumption = annual_bill / tariff

            # Approximate system size estimation
            average_specific_yield = 1500  # kWh per kW per year (India average)
            estimated_system_size = annual_consumption / average_specific_yield
            estimated_area = estimated_system_size / 0.18

            metrics, monthly_generation = estimate_solar_metrics(
                area_m2=estimated_area,
                latitude=latitude,
                longitude=longitude,
                tilt=tilt,
                azimuth=azimuth,
                optimize=optimize,
                tariff=tariff
            )

            display_results(metrics, monthly_generation)


# ROOFTOP MODE

elif input_mode == "Rooftop Image (AI Detection)":

    st.header("Upload Rooftop Image")

    uploaded_file = st.file_uploader(
        "Upload a satellite or aerial rooftop image",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:

        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Image", use_container_width=True)

        with st.spinner("Detecting rooftop area..."):
            sam = load_cached_sam()
            mask = get_rooftop_mask(image, sam)

        if mask is None:
            st.error("Rooftop could not be detected. Please upload a clearer image.")
        else:
            masked_image_np = np.array(image)
            masked_image_np[~mask] = [0, 0, 0]

            st.image(masked_image_np, caption="Detected Rooftop Area", use_container_width=True)

            area_m2 = calculate_area_from_mask(mask)

            metrics, monthly_generation = estimate_solar_metrics(
                area_m2=area_m2,
                latitude=latitude,
                longitude=longitude,
                tilt=tilt,
                azimuth=azimuth,
                optimize=optimize,
                tariff=tariff
            )

            display_results(metrics, monthly_generation)

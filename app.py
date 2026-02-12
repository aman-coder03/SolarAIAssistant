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

def display_results(metrics, monthly_generation, monthly_bill=None, tariff=8.0):

    st.markdown("## Solar Feasibility Summary")

    system_size = metrics["system_size_kw"]
    annual_gen = metrics["annual_generation_kwh"]
    annual_savings = metrics["annual_savings"]
    payback = metrics["payback_years"]
    roi = metrics["roi_percent"]
    net_cost = metrics["net_cost"]

    # --- Bill Offset ---
    if monthly_bill:
        annual_consumption = (monthly_bill * 12) / tariff
        bill_offset = min((annual_gen / annual_consumption) * 100, 100)
        estimated_new_bill = max(
            (annual_consumption - annual_gen) * tariff / 12, 0
        )
    else:
        bill_offset = None
        estimated_new_bill = None

    # WHAT THIS MEANS FOR YOU

    st.markdown("### What This Means For You")

    col1, col2, col3 = st.columns(3)

    col1.metric("System Size", f"{system_size} kW")
    col2.metric("Annual Savings", f"₹{annual_savings:,.0f}")
    col3.metric("Payback Period", f"{payback} years")

    if bill_offset:
        st.success(
            f"Your solar system can offset **{bill_offset:.0f}%** of your yearly electricity usage."
        )
        st.info(
            f"Your ₹{monthly_bill:,.0f} monthly bill could reduce to approximately **₹{estimated_new_bill:,.0f}/month**."
        )

    # LONG TERM VALUE

    st.markdown("### 10-Year Financial Impact")

    total_10yr = metrics["cumulative_savings"][-1]

    st.write(
        f"Over 10 years, you could save approximately **₹{total_10yr:,.0f}**."
    )

    if roi > 25:
        st.success("This investment significantly outperforms fixed deposits and low-risk instruments.")
    elif roi > 15:
        st.warning("This provides moderate long-term financial benefit.")
    else:
        st.error("Financial return is relatively modest under current assumptions.")

    with st.expander("Technical Details (Advanced Users)"):
        st.write(f"Annual Generation: {annual_gen} kWh")
        st.write(f"Performance Ratio: {metrics['performance_ratio']}")
        st.write(f"Installation Cost: ₹{metrics['installation_cost']}")
        st.write(f"Subsidy (PM Surya Ghar): ₹{metrics['subsidy']}")
        st.write(f"Net Cost After Subsidy: ₹{net_cost}")

    # Side-by-side plots
    st.subheader("Energy & Financial Projection")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Monthly Energy Output")
        fig1, ax1 = plt.subplots(figsize=(5, 3))
        ax1.bar(monthly_generation.index.strftime("%b"), 
                monthly_generation.values)
        ax1.set_ylabel("Energy (kWh)")
        ax1.set_xlabel("Month")
        plt.tight_layout()
        st.pyplot(fig1)

    with col2:
        st.markdown("### 10-Year Savings Projection")
        fig2, ax2 = plt.subplots(figsize=(5, 3))
        ax2.plot(range(1, 11), metrics["cumulative_savings"], marker="o")
        ax2.set_ylabel("Cumulative Savings (₹)")
        ax2.set_xlabel("Year")
        plt.tight_layout()
        st.pyplot(fig2)


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
            utilization_factor = 0.7
            estimated_area = (estimated_system_size / 0.18) / utilization_factor

            metrics, monthly_generation = estimate_solar_metrics(
                area_m2=estimated_area,
                latitude=latitude,
                longitude=longitude,
                tilt=tilt,
                azimuth=azimuth,
                optimize=optimize,
                tariff=tariff
            )

            display_results(
                metrics,
                monthly_generation,
                monthly_bill=monthly_bill,
                tariff=tariff
            )


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

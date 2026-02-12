import numpy as np
from solar_engine import run_full_simulation


# -------------------------------------------------------
# Rooftop Area Calculation
# -------------------------------------------------------

def calculate_area_from_mask(mask, resolution=0.1):
    """
    Estimate rooftop area in square meters.
    resolution = meters per pixel
    """
    pixel_count = np.sum(mask)
    return round(pixel_count * (resolution ** 2), 2)


# -------------------------------------------------------
# PM Surya Ghar Subsidy Model
# -------------------------------------------------------

def calculate_pm_surya_subsidy(system_size_kw, cost_per_kw):
    """
    PM Surya Ghar subsidy rules:
    - 40% subsidy up to 3 kW
    - 20% subsidy for 3–10 kW
    """

    if system_size_kw <= 3:
        subsidy = system_size_kw * cost_per_kw * 0.40
    elif system_size_kw <= 10:
        subsidy = (
            3 * cost_per_kw * 0.40 +
            (system_size_kw - 3) * cost_per_kw * 0.20
        )
    else:
        subsidy = (
            3 * cost_per_kw * 0.40 +
            7 * cost_per_kw * 0.20
        )

    return int(subsidy)


# -------------------------------------------------------
# 10-Year Financial Projection
# -------------------------------------------------------

def ten_year_projection(annual_generation_kwh, tariff):
    """
    Includes:
    - 0.5% annual panel degradation
    - 5% annual tariff inflation
    """

    degradation_rate = 0.005
    inflation_rate = 0.05

    yearly_savings = []
    cumulative_savings = []
    cumulative = 0

    for year in range(1, 11):

        adjusted_generation = annual_generation_kwh * ((1 - degradation_rate) ** year)
        adjusted_tariff = tariff * ((1 + inflation_rate) ** year)

        savings = adjusted_generation * adjusted_tariff
        cumulative += savings

        yearly_savings.append(round(savings, 2))
        cumulative_savings.append(round(cumulative, 2))

    return yearly_savings, cumulative_savings


# -------------------------------------------------------
# Main Solar Estimation Function
# -------------------------------------------------------

def estimate_solar_metrics(
    area_m2,
    latitude,
    longitude,
    tilt,
    azimuth,
    optimize,
    tariff=8.0,
    cost_per_kw=55000
):

    if area_m2 <= 0:
        raise ValueError("Detected rooftop area is zero.")

    # ---- System sizing ----
    module_efficiency = 0.18
    system_size_kw = round(area_m2 * module_efficiency, 2)

    if system_size_kw <= 0:
        system_size_kw = 0.1

    # ---- pvlib Simulation ----
    results = run_full_simulation(
        latitude,
        longitude,
        system_size_kw,
        tilt,
        azimuth
    )

    annual_generation_kwh = results["annual_real_kwh"]

    # ---- Installation Cost (India) ----
    installation_cost = int(system_size_kw * cost_per_kw)

    # ---- PM Surya Ghar Subsidy ----
    subsidy = calculate_pm_surya_subsidy(system_size_kw, cost_per_kw)
    net_cost = installation_cost - subsidy

    # ---- Annual Savings ----
    annual_savings = round(annual_generation_kwh * tariff, 2)

    # ---- Payback Calculation ----
    if annual_savings > 0:
        payback_years = round(net_cost / annual_savings, 1)
        roi = round((annual_savings / net_cost) * 100, 1)
    else:
        payback_years = float("inf")
        roi = 0

    # ---- 10-Year Projection ----
    yearly_savings, cumulative_savings = ten_year_projection(
        annual_generation_kwh,
        tariff
    )

    metrics = {
        "system_size_kw": system_size_kw,
        "annual_generation_kwh": round(annual_generation_kwh, 2),
        "annual_clear_kwh": results["annual_clear_kwh"],
        "weather_loss_percent": results["weather_loss_percent"],
        "performance_ratio": results["performance_ratio"],
        "installation_cost": installation_cost,
        "subsidy": subsidy,
        "net_cost": net_cost,
        "annual_savings": annual_savings,
        "payback_years": payback_years,
        "roi_percent": roi,
        "yearly_savings": yearly_savings,
        "cumulative_savings": cumulative_savings
    }

    return metrics, results["monthly_generation"]

import numpy as np
from solar_engine import run_full_simulation


def calculate_area_from_mask(mask, resolution=0.1):
    """
    Estimate rooftop area in m².
    resolution = meters per pixel
    """
    pixel_count = np.sum(mask)
    return round(pixel_count * (resolution ** 2), 2)


def estimate_solar_metrics(area_m2, latitude, longitude, tilt, azimuth, optimize):

    # ---- Basic sanity guard ----
    if area_m2 <= 0:
        raise ValueError("Detected rooftop area is zero.")

    # ---- System sizing ----
    module_efficiency = 0.18  # 18% realistic module efficiency
    system_size_kw = round(area_m2 * module_efficiency, 2)

    if system_size_kw <= 0:
        system_size_kw = 0.1  # minimum small system fallback

    # ---- Run full pvlib simulation ----
    results = run_full_simulation(
        latitude,
        longitude,
        system_size_kw,
        tilt,
        azimuth
    )

    annual_generation_kwh = results["annual_real_kwh"]

    # ---- Avoid divide-by-zero ----
    if system_size_kw > 0:
        specific_yield = round(annual_generation_kwh / system_size_kw, 2)
    else:
        specific_yield = 0

    # ---- Financial modeling ----
    installation_cost = int(system_size_kw * 1000)  # $1000/kW
    annual_savings = int(annual_generation_kwh * 0.12)  # $0.12/kWh

    if annual_savings > 0:
        payback_years = round(installation_cost / annual_savings, 1)
        roi = round((annual_savings / installation_cost) * 100, 1)
    else:
        payback_years = float("inf")
        roi = 0

    metrics = {
        "system_size_kw": system_size_kw,
        "annual_generation_kwh": round(annual_generation_kwh, 2),
        "annual_clear_kwh": results["annual_clear_kwh"],
        "weather_loss_percent": results["weather_loss_percent"],
        "performance_ratio": results["performance_ratio"],
        "specific_yield": specific_yield,
        "installation_cost": installation_cost,
        "annual_savings": annual_savings,
        "payback_years": payback_years,
        "roi_percent": roi
    }

    return metrics, results["monthly_generation"]

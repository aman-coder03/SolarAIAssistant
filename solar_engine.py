import pvlib
import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from meteostat import Point, hourly
from datetime import datetime


def get_temperature_data(latitude, longitude, times):

    location = Point(latitude, longitude)

    start = times[0].tz_localize(None).to_pydatetime()
    end = times[-1].tz_localize(None).to_pydatetime()

    ts = hourly(location, start, end)
    data = ts.fetch()

    # ---- If meteostat returns nothing ----
    if data is None or data.empty:
        data = pd.DataFrame(index=times)
        data["temp_air"] = 25
        data["wind_speed"] = 1
        return data

    # ---- Only rename AFTER confirming data exists ----
    data = data.rename(columns={
        "temp": "temp_air",
        "wspd": "wind_speed"
    })

    data = data.reindex(times).interpolate()

    return data


def build_system(system_size_kw, tilt, azimuth, dc_ac_ratio=1.2):

    modules = pvlib.pvsystem.retrieve_sam("CECMod")
    inverters = pvlib.pvsystem.retrieve_sam("cecinverter")

    # Highest efficiency module
    modules_sorted = modules.T.sort_values("STC", ascending=False)
    module = modules_sorted.iloc[0]

    module_power = module["STC"] / 1000

    # DC sizing
    modules_per_string = 10
    strings = max(int(system_size_kw / (module_power * modules_per_string)), 1)

    # AC sizing based on DC/AC ratio
    inverter_target_kw = system_size_kw / dc_ac_ratio

    inverters_t = inverters.T
    inverters_t["ac_kw"] = inverters_t["Pdco"] / 1000

    inverter = inverters_t.iloc[
        (inverters_t["ac_kw"] - inverter_target_kw).abs().argsort()[:1]
    ].iloc[0]

    system = PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=module,
        inverter_parameters=inverter,
        modules_per_string=modules_per_string,
        strings_per_inverter=strings,
        racking_model="open_rack",
        module_type="glass_polymer"
    )

    return system


def run_full_simulation(latitude, longitude, system_size_kw, tilt=20, azimuth=180):

    site = Location(latitude, longitude, tz="Asia/Kolkata")

    times = pd.date_range(
        start="2024-01-01 00:00",
        end="2024-12-31 23:00",
        freq="1h",
        tz=site.tz
    )

    # Clear-sky irradiance
    clearsky = site.get_clearsky(times, model="ineichen")

    # Add real temperature data
    temperature = get_temperature_data(latitude, longitude, times)

    weather = clearsky.copy()

    # Apply realistic India atmospheric reduction
    real_world_factor = 1.0
    weather[["ghi", "dni", "dhi"]] *= real_world_factor
    
    weather["temp_air"] = temperature["temp_air"]
    weather["wind_speed"] = temperature.get("wind_speed", 1)

    system = build_system(system_size_kw, tilt, azimuth, dc_ac_ratio=1.2)

    mc = ModelChain(
        system,
        site,
        aoi_model="physical",
        spectral_model="no_loss",
        temperature_model="sapm"
    )
    mc.run_model(weather)
    ac = mc.results.ac.fillna(0)

    system_losses = 0.15  # 15% realistic losses
    ac_adjusted = ac * (1 - system_losses)

    annual_real = ac_adjusted.sum() / 1000
    monthly_real = ac_adjusted.resample("ME").sum() / 1000

    # Clear-sky ideal comparison
    mc_clear = ModelChain(
        system,
        site,
        aoi_model="physical",
        spectral_model="no_loss",
        temperature_model="sapm"
    )
    mc_clear.run_model(clearsky)

    ac_clear = mc_clear.results.ac.fillna(0)
    annual_clear = ac_clear.sum() / 1000

    poa = mc.results.total_irrad["poa_global"]  # W/m²
    poa_sum = poa.sum() / 1000  # kWh/m²

    if system_size_kw > 0 and poa_sum > 0:
        pr = annual_real / (system_size_kw * poa_sum)
    else:
        pr = 0

    if annual_clear > 0:
        weather_loss_percent = round(
            ((annual_clear - annual_real) / annual_clear) * 100, 2
        )
    else:
        weather_loss_percent = 0

    return {
        "annual_real_kwh": round(annual_real, 2),
        "annual_clear_kwh": round(annual_clear, 2),
        "weather_loss_percent": weather_loss_percent,
        "performance_ratio": round(pr, 3),
        "monthly_generation": monthly_real
    }

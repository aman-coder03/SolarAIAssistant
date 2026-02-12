import pvlib
import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from meteostat import Point
from meteostat import hourly
from datetime import datetime


def get_temperature_data(latitude, longitude, times):

    location = Point(latitude, longitude)
    start = times[0].to_pydatetime()
    end = times[-1].to_pydatetime()

    data = hourly.Hourly(location, start, end).fetch()


    data = data.rename(columns={
        "temp": "temp_air",
        "wspd": "wind_speed"
    })

    data = data.reindex(times).interpolate()

    return data


def build_system(system_size_kw, tilt, azimuth):

    modules = pvlib.pvsystem.retrieve_sam("CECMod")
    inverters = pvlib.pvsystem.retrieve_sam("cecinverter")

    module = modules["JA_Solar_JAM60S20_385_MR"]  # ~385W modern module
    inverter = inverters["SMA_America__SB5000TL_US_240V_"]  # ~5 kW inverter

    module_power = module["STC"] / 1000  # kW per module
    num_modules = max(int(system_size_kw / module_power), 1)

    dc_ac_ratio = 1.2
    inverter_ac_kw = inverter["Pdco"] / 1000

    target_dc_kw = system_size_kw
    target_ac_kw = target_dc_kw / dc_ac_ratio

    modules_per_string = 10
    strings = max(int(target_dc_kw / (module_power * modules_per_string)), 1)

    system = PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=module,
        inverter_parameters=inverter,
        modules_per_string=modules_per_string,
        strings_per_inverter=strings,
        losses_parameters={"soiling": 2, "wiring": 2, "mismatch": 2}
    )

    return system


def run_full_simulation(latitude, longitude, system_size_kw, tilt=20, azimuth=180):

    site = Location(latitude, longitude, tz="Asia/Kolkata")

    times = pd.date_range(
        start="2024-01-01 00:00",
        end="2024-12-31 23:00",
        freq="1H",
        tz=site.tz
    )

    # Clear-sky irradiance
    clearsky = site.get_clearsky(times)

    # Add real temperature data
    temperature = get_temperature_data(latitude, longitude, times)

    weather = clearsky.copy()
    weather["temp_air"] = temperature["temp_air"]
    weather["wind_speed"] = temperature.get("wind_speed", 1)

    system = build_system(system_size_kw, tilt, azimuth)

    mc = ModelChain(
        system,
        site,
        aoi_model="physical",
        spectral_model="no_loss",
        temperature_model="sapm"
    )
    mc.run_model(weather)

    ac = mc.results.ac.fillna(0)

    annual_real = ac.sum() / 1000
    monthly_real = ac.resample("M").sum() / 1000

    # Clear-sky ideal comparison
    mc_clear = ModelChain(system, site)
    mc_clear.run_model(clearsky)

    ac_clear = mc_clear.results.ac.fillna(0)
    annual_clear = ac_clear.sum() / 1000

    # Extra losses
    extra_losses = 0.08  # 8% more realistic India assumption
    annual_real_adjusted = annual_real * (1 - extra_losses)

    # Performance ratio
    poa = mc.results.total_irrad["poa_global"]
    poa_sum = poa.sum() / 1000  # kWh/m2

    if poa_sum > 0:
        pr = annual_real / (system_size_kw * poa_sum)
    else:
        pr = 0

    if annual_clear > 0:
        weather_loss_percent = round(
            ((annual_clear - annual_real_adjusted) / annual_clear) * 100, 2
        )
    else:
        weather_loss_percent = 0

    return {
        "annual_real_kwh": round(annual_real_adjusted, 2),
        "annual_clear_kwh": round(annual_clear, 2),
        "weather_loss_percent": weather_loss_percent,
        "performance_ratio": round(pr, 3),
        "monthly_generation": monthly_real
    }

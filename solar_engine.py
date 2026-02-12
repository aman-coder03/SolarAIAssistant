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

    module = modules["Canadian_Solar_CS5P_220M___2009_"]
    inverter = inverters["ABB__MICRO_0_25_I_OUTD_US_208__208V_"]

    module_power = module["STC"] / 1000  # kW per module
    num_modules = max(int(system_size_kw / module_power), 1)

    system = PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=module,
        inverter_parameters=inverter,
        modules_per_string=10,
        strings_per_inverter=max(int(num_modules / 10), 1),
    )

    return system


def run_full_simulation(latitude, longitude, system_size_kw, tilt=20, azimuth=180):

    site = Location(latitude, longitude, tz="Asia/Kolkata")

    times = pd.date_range(
        start="2024-01-01",
        end="2024-12-31",
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

    mc = ModelChain(system, site)
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
    extra_losses = 0.05  # 5%
    annual_real_adjusted = annual_real * (1 - extra_losses)

    # Performance ratio
    poa = mc.results.total_irrad["poa_global"].sum()  # Wh/m2
    if poa > 0:
        pr = annual_real_adjusted / (system_size_kw * (poa / 1000))
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

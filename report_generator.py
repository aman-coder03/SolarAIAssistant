from fpdf import FPDF
import datetime
import os


def generate_pdf_report(output_path, image_path, area, metrics):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "SolarAIAssistant Report", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Date: {datetime.datetime.now()}", ln=True)

    if image_path:
        pdf.image(image_path, x=40, y=30, w=130)
        pdf.ln(85)

    pdf.cell(200, 10, f"Rooftop Area: {area} m²", ln=True)
    pdf.cell(200, 10, f"System Size: {metrics['system_size_kw']} kW", ln=True)
    pdf.cell(200, 10, f"Annual Generation: {metrics['annual_generation_kwh']} kWh", ln=True)
    pdf.cell(200, 10, f"Tilt Used: {metrics['tilt_used']}°", ln=True)
    pdf.cell(200, 10, f"Specific Yield: {metrics['specific_yield']} kWh/kWp", ln=True)
    pdf.cell(200, 10, f"CO2 Offset: {metrics['co2_offset_tons']} tons/year", ln=True)
    pdf.cell(200, 10, f"Installation Cost: ${metrics['installation_cost']}", ln=True)
    pdf.cell(200, 10, f"Annual Savings: ${metrics['annual_savings']}", ln=True)
    pdf.cell(200, 10, f"Payback Period: {metrics['payback_years']} years", ln=True)
    pdf.cell(200, 10, f"ROI: {metrics['roi_percent']}%", ln=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path

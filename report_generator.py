from fpdf import FPDF
import datetime
import os


def generate_pdf_report(output_path, image_path, area, metrics):

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "SolarAIAssistant Report", ln=True, align="C")

    # Date
    pdf.set_font("Arial", size=12)
    pdf.ln(8)
    pdf.cell(
        200,
        10,
        f"Date: {datetime.datetime.now().strftime('%d-%m-%Y')}",
        ln=True
    )

    pdf.ln(5)

    # Rooftop image (if provided)
    if image_path and os.path.exists(image_path):
        pdf.image(image_path, x=30, w=150)
        pdf.ln(85)

    # Technical Details
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "System Overview", ln=True)
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 8, f"Usable Rooftop Area: {area} m²", ln=True)
    pdf.cell(200, 8, f"System Size: {metrics['system_size_kw']} kW", ln=True)
    pdf.cell(200, 8, f"Annual Energy Generation: {metrics['annual_generation_kwh']} kWh", ln=True)
    pdf.cell(200, 8, f"Performance Ratio: {metrics['performance_ratio']}", ln=True)
    pdf.cell(200, 8, f"Weather Loss: {metrics['weather_loss_percent']}%", ln=True)

    pdf.ln(5)

    # Financial Details
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Financial Summary (PM Surya Ghar)", ln=True)
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 8, f"Estimated Installation Cost: ₹{metrics['installation_cost']}", ln=True)
    pdf.cell(200, 8, f"Estimated Subsidy: ₹{metrics['subsidy']}", ln=True)
    pdf.cell(200, 8, f"Net Cost After Subsidy: ₹{metrics['net_cost']}", ln=True)
    pdf.cell(200, 8, f"Estimated Annual Savings: ₹{metrics['annual_savings']}", ln=True)
    pdf.cell(200, 8, f"Estimated Payback Period: {metrics['payback_years']} years", ln=True)
    pdf.cell(200, 8, f"Estimated ROI: {metrics['roi_percent']}%", ln=True)

    pdf.ln(5)

    # 10-Year Projection Summary
    if "cumulative_savings" in metrics:
        total_10yr_savings = round(metrics["cumulative_savings"][-1], 2)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "10-Year Projection", ln=True)
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 8, f"Projected 10-Year Savings: ₹{total_10yr_savings}", ln=True)

    # Save file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)

    return output_path

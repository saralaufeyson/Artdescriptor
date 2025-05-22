import streamlit as st
import openai
import base64
from PIL import Image
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile
from reportlab.platypus import Paragraph, Frame, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from dotenv import load_dotenv

# Set your OpenAI API key from key.txt
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Painting Listing Generator", layout="centered")
st.title("🖼️ Painting Listing Generator for Amazon")
st.markdown("Upload a painting image and enter details to generate a professional product description and features.")

col1,col2 = st.columns([1,2])
# Upload image
with col1:
    uploaded_file = st.file_uploader("📤 Upload Painting Image", type=["jpg", "jpeg", "png"])

# Display resized image preview
with col2:
    if uploaded_file:
        st.image(uploaded_file, caption="🖼️ Uploaded Painting", width=300)

# Limit file size to 10MB
if uploaded_file is not None:
    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)
    if file_size > 5 * 1024 * 1024:
        st.error("File size exceeds 5MB. Please upload a smaller image.")
        uploaded_file = None

# Inputs
title = st.text_input("🎨 Painting Title")
size = st.text_input("📏 Size (e.g. 24x36 inches)")
medium = st.text_input("🖌️ Medium (e.g. Acrylic on canvas)")

# Convert image to base64
def convert_image_to_base64(uploaded_file):
    image_bytes = uploaded_file.read()
    return base64.b64encode(image_bytes).decode('utf-8')

# Generate listing using GPT
def generate_listing(image_base64, title, size, medium):
    prompt = (
        f"You are a professional Amazon product copywriter for fine art. "
        f"You are good in writing and always give both Indian and international touch accordingly.\n"
        f"Generate a persuasive product listing for the painting below.\n\n"
        f"You are going to sell the copies on print-on-demand in 3 sizes - original, small and large.\n\n"
        f"Title: {title}\n"
        f"Size: {size}\n"
        f"Medium: {medium}\n\n"
        f"Tasks:\n"
        f"1. Write a product description (2 paragraphs or 100 words) to attract buyers.\n"
        f"2. Provide 5 bullet points for Amazon, covering:\n"
        f"   - Material & craftsmanship\n"
        f"   - Style & visual appeal\n"
        f"   - Room suitability\n"
        f"   - Emotional impact\n"
        f"   - Gift potential"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        max_tokens=800,
        messages=[
            {"role": "system", "content": "You are an expert art marketing copywriter for e-commerce."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    }
                ]
            }
        ]
    )
    return response['choices'][0]['message']['content']

# Extract description and bullet points
def extract_description_and_bullets(full_text):
    lines = full_text.strip().split("\n")
    description_lines = []
    bullet_lines = []
    in_bullets = False
    for line in lines:
        if line.strip().startswith("•") or line.strip().startswith("-"):
            in_bullets = True
        if in_bullets:
            bullet_lines.append(line)
        else:
            description_lines.append(line)
    return description_lines, "\n".join(bullet_lines).strip()

# Generate Listing Button
if st.button("🚀 Generate Listing"):
    if not uploaded_file or not title or not size or not medium:
        st.warning("Please fill in all fields and upload an image.")
    else:
        with st.spinner("Analyzing image and generating description..."):
            image_base64 = convert_image_to_base64(uploaded_file)
            description_lines, bullets = extract_description_and_bullets(
                generate_listing(image_base64, title, size, medium)
            )
            st.session_state.description_lines = description_lines
            st.session_state.bullets = bullets
        st.success("✅ Listing generated! You can now export as PDF.")

# Always display description and bullets if present in session_state
if "description_lines" in st.session_state and st.session_state.description_lines:
    st.subheader("📄 Product Description")
    for line in st.session_state.description_lines:
        st.write(line)

if "bullets" in st.session_state and st.session_state.bullets:
    st.subheader("🔹 Amazon Bullet Points")
    st.markdown(st.session_state.bullets)

# Prices
st.subheader("💰 Enter Prices for Variants")
price_original = st.number_input("Original Price (₹)", min_value=0, step=100)
price_small = st.number_input("Small Variant Price (₹)", min_value=0, step=100)
price_large = st.number_input("Large Variant Price (₹)", min_value=0, step=100)

# Calculate variant sizes
def calculate_variant_sizes(original_size):
    try:
        width, height = map(float, original_size.lower().replace("inches", "").split("x"))
        return {
            "Original": f"{width:.1f} x {height:.1f} inches",
            "Small": f"{width * 0.75:.1f} x {height * 0.75:.1f} inches",
            "Large": f"{width * 1.5:.1f} x {height * 1.5:.1f} inches"
        }
    except:
        return {"Original": original_size, "Small": "N/A", "Large": "N/A"}

variant_sizes = calculate_variant_sizes(size)

# Generate PDF
def generate_pdf(image_file, title, medium, sizes, prices, description_lines, bullets):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp_file.name, pagesize=A4)
    width, height = A4
    margin = 40

    # Draw border
    c.setStrokeColor(colors.HexColor("#444444"))
    c.setLineWidth(2)
    c.rect(margin/2, margin/2, width - margin, height - margin)

    y = height - margin

    # Header
    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(0.1, 0.3, 0.4)
    c.drawCentredString(width / 2, y - 20, "Sasirekha Creations")
    c.setFillColorRGB(0, 0, 0)
    y -= 50

    # Title above image
    c.setFont("Times-Bold", 16)
    c.drawString(margin, y, f"Painting Name: {title}")
    y -= 25

    # Image
    img = Image.open(image_file)
    img.thumbnail((300, 200))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    img_x = margin
    img_y = y - 200
    c.drawImage(ImageReader(bio), img_x, img_y, width=300, height=200, preserveAspectRatio=True)
    # Watermark
    c.saveState()
    c.translate(img_x + 90, img_y + 50)
    c.rotate(30)
    c.setFont("Times-Bold", 20)
    c.setFillColorRGB(0.8, 0.8, 0.8, alpha=0.5)
    c.drawCentredString(0, 0, "Artree")
    c.restoreState()
    y = img_y - 20

    # Medium
    c.setFont("Times-Roman", 12)
    c.drawString(margin, y, f"Medium: {medium}")
    y -= 20

    # Sizes & Prices
    c.setFont("Times-Bold", 12)
    c.drawString(margin, y, "Variants:")
    y -= 20

    # Prepare table data
    table_data = [["Variant", "Size", "Price (₹)"]]
    for label in ["Original", "Small", "Large"]:
        table_data.append([label, sizes[label], f"{prices[label]:,}"])

    # Create table
    table = Table(table_data, colWidths=[70, 130, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#222222")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")),
    ]))

    # Calculate table height
    table_width, table_height = table.wrapOn(c, width - 2*margin, 60)
    table.drawOn(c, margin, y - table_height)
    y -= table_height + 10

    # Prepare styles for Paragraphs
    styles = getSampleStyleSheet()
    desc_style = ParagraphStyle(
        'desc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=0,
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        'bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leftIndent=15,
        bulletIndent=5,
        leading=13,
        spaceAfter=2,
    )

    # Description as formatted text (not markdown)
    y -= 5
    c.setFont("Times-Bold", 12)
    c.drawString(margin, y, "Description:")
    y -= 15

    desc_width = width - 2*margin
    styles = getSampleStyleSheet()
    desc_style = ParagraphStyle(
        'desc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=0,
        spaceAfter=8,
    )
    desc_paragraphs = [Paragraph(line, desc_style) for line in description_lines if line.strip()]
    total_height = 0
    for para in desc_paragraphs:
        _, h = para.wrap(desc_width, 1000)
        total_height += h + 2
    desc_frame_height = total_height + 5
    desc_frame = Frame(margin, y - desc_frame_height, desc_width, desc_frame_height, showBoundary=0)
    desc_frame.addFromList(desc_paragraphs, c)
    y = y - desc_frame_height - 5

    # Bullets as formatted text
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Key Features:")
    y -= 15

    # Prepare bullet points as Paragraphs
    bullet_items = []
    for line in bullets.split("\n"):
        line = line.strip('•- ').strip()
        if line:
            bullet_items.append(Paragraph(f"&bull; {line}", bullet_style))

    # Dynamically calculate required height for all bullet points
    bullet_total_height = 0
    for para in bullet_items:
        _, h = para.wrap(width - 2*margin, 1000)
        bullet_total_height += h + 2
    bullet_frame_height = bullet_total_height + 5

    # Ensure the frame does not go below the margin
    bullet_frame_height = min(bullet_frame_height, y - margin - 10)
    bullet_frame = Frame(margin, y - bullet_frame_height, width - 2*margin, bullet_frame_height, showBoundary=0)
    bullet_frame.addFromList(bullet_items, c)

    c.showPage()
    c.save()
    return tmp_file.name

# Export PDF Button
if st.button("🧾 Export as A4 PDF"):
    if not price_original or not price_small or not price_large:
        st.warning("Please fill in all prices.")
    elif "description_lines" not in st.session_state or "bullets" not in st.session_state:
        st.warning("Please generate the listing before exporting.")
    else:
        prices = {
            "Original": price_original,
            "Small": price_small,
            "Large": price_large
        }
        pdf_path = generate_pdf(
            uploaded_file, title, medium,
            variant_sizes, prices,
            st.session_state.description_lines,
            st.session_state.bullets
        )
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", data=f, file_name=f"{title}_listing.pdf", mime="application/pdf")

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
import hashlib
from pymongo import MongoClient

# Use Streamlit secrets for sensitive keys
openai.api_key = st.secrets["OPENAI_API_KEY"]
MONGO_URI = st.secrets["MONGO_URI"]

# Streamlit config
st.set_page_config(page_title="Painting Listing Generator", layout="centered")
st.title("🖼️ Painting Listing Generator for Amazon")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["arttree"]
collection = db["paintings"]

# Utility functions
def convert_image_to_base64(uploaded_file):
    image_bytes = uploaded_file.read()
    return base64.b64encode(image_bytes).decode('utf-8')

def hash_image(uploaded_file):
    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.sha256(image_bytes).hexdigest()

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

def generate_listing(image_base64, title, size, medium):
    prompt = (
        f"You are a professional Amazon product copywriter for fine art...\n"
        f"Title: {title}\nSize: {size}\nMedium: {medium}..."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        max_tokens=800,
        messages=[
            {"role": "system", "content": "You are an expert art marketing copywriter for e-commerce."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ]
    )
    return response['choices'][0]['message']['content']

def extract_description_and_bullets(full_text):
    lines = full_text.strip().split("\n")
    description_lines, bullet_lines = [], []
    in_bullets = False
    for line in lines:
        if line.strip().startswith("•") or line.strip().startswith("-"):
            in_bullets = True
        (bullet_lines if in_bullets else description_lines).append(line)
    return description_lines, "\n".join(bullet_lines).strip()

def generate_pdf(image_file, title, medium, sizes, prices, description_lines, bullets, painting_id=None):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp_file.name, pagesize=A4)
    width, height = A4
    margin = 40

    # Draw border and header
    c.setStrokeColor(colors.HexColor("#444444"))
    c.setLineWidth(2)
    c.rect(margin/2, margin/2, width - margin, height - margin)
    y = height - margin
    c.setFont("Times-Bold", 18)
    c.drawCentredString(width / 2, y - 20, "Sasirekha Creations")
    y -= 50

    if painting_id:
        c.setFont("Times-Roman", 10)
        c.drawString(margin, y, f"Painting ID: {painting_id}")
        y -= 18

    c.setFont("Times-Bold", 16)
    c.drawString(margin, y, f"Painting Name: {title}")
    y -= 25

    img = Image.open(image_file)
    img.thumbnail((300, 200))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    c.drawImage(ImageReader(bio), margin, y - 200, width=300, height=200, preserveAspectRatio=True)
    c.saveState()
    c.translate(margin + 90, y - 150)
    c.rotate(30)
    c.setFont("Times-Bold", 20)
    c.setFillColorRGB(0.8, 0.8, 0.8, alpha=0.5)
    c.drawCentredString(0, 0, "Artree")
    c.restoreState()
    y -= 220

    c.setFont("Times-Roman", 12)
    c.drawString(margin, y, f"Medium: {medium}")
    y -= 20

    c.setFont("Times-Bold", 12)
    c.drawString(margin, y, "Variants:")
    y -= 20

    table_data = [["Variant", "Size", "Price (₹)"]] + [
        [k, sizes[k], f"{prices[k]:,}"] for k in ["Original", "Small", "Large"]
    ]
    table = Table(table_data, colWidths=[70, 130, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")),
    ]))
    table_width, table_height = table.wrapOn(c, width - 2 * margin, 60)
    table.drawOn(c, margin, y - table_height)
    y -= table_height + 10

    desc_style = ParagraphStyle('desc', fontName='Helvetica', fontSize=10, leading=13)
    bullet_style = ParagraphStyle('bullet', fontName='Helvetica', fontSize=10, leftIndent=15, bulletIndent=5)

    y -= 5
    c.setFont("Times-Bold", 12)
    c.drawString(margin, y, "Description:")
    y -= 15

    desc_paragraphs = [Paragraph(line, desc_style) for line in description_lines if line.strip()]
    total_height = sum([para.wrap(width - 2 * margin, 1000)[1] for para in desc_paragraphs]) + 5
    desc_frame = Frame(margin, y - total_height, width - 2 * margin, total_height, showBoundary=0)
    desc_frame.addFromList(desc_paragraphs, c)
    y -= total_height + 5

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Key Features:")
    y -= 15

    bullet_items = [Paragraph(f"&bull; {line.strip('•- ').strip()}", bullet_style) for line in bullets.split("\n") if line.strip()]
    bullet_total_height = sum([p.wrap(width - 2 * margin, 1000)[1] for p in bullet_items]) + 5
    bullet_frame_height = min(bullet_total_height, y - margin - 10)
    bullet_frame = Frame(margin, y - bullet_frame_height, width - 2 * margin, bullet_frame_height, showBoundary=0)
    bullet_frame.addFromList(bullet_items, c)

    c.showPage()
    c.save()
    return tmp_file.name

# UI Layout
st.markdown("Upload a painting image and enter details to generate a professional product description and features.")
col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("📤 Upload Painting Image", type=["jpg", "jpeg", "png"])
with col2:
    if uploaded_file:
        st.image(uploaded_file, caption="🖼️ Uploaded Painting", width=250)

# Input validation
if uploaded_file:
    uploaded_file.seek(0, os.SEEK_END)
    if uploaded_file.tell() > 5 * 1024 * 1024:
        st.error("File size exceeds 5MB.")
        uploaded_file = None
    uploaded_file.seek(0)

title = st.text_input("🎨 Painting Title")
painting_id = st.text_input("🆔 Painting ID (required)")
size = st.text_input("📏 Size (e.g. 24x36 inches)")
medium = st.text_input("🖌️ Medium (e.g. Acrylic on canvas)")
price_original = st.number_input("Original Price (₹)", min_value=0, step=100)
price_small = st.number_input("Small Variant Price (₹)", min_value=0, step=100)
price_large = st.number_input("Large Variant Price (₹)", min_value=0, step=100)

# Sidebar History
with st.sidebar:
    st.header("🕑 View History")
    history = list(collection.find({}, {"_id": 0, "title": 1, "image_hash": 1}))
    selected = st.selectbox("Select a previous listing", ["-"] + [h["title"] for h in history])
    if selected and selected != "-":
        doc = collection.find_one({"title": selected})
        if doc:
            st.session_state.update(doc)
            st.success(f"Loaded listing for {selected}")

# Generate Listing
if st.button("🚀 Generate Listing"):
    if not all([uploaded_file, title, size, medium, painting_id]):
        st.warning("Please complete all fields and upload an image.")
    else:
        image_hash = hash_image(uploaded_file)
        existing = collection.find_one({"image_hash": image_hash})
        if existing:
            st.session_state.update(existing)
            st.success("✅ Loaded existing listing.")
        else:
            with st.spinner("Generating listing..."):
                image_base64 = convert_image_to_base64(uploaded_file)
                desc_lines, bullets = extract_description_and_bullets(generate_listing(image_base64, title, size, medium))
                variants = calculate_variant_sizes(size)
                st.session_state.update({
                    "description_lines": desc_lines,
                    "bullets": bullets,
                    "painting_id": painting_id,
                    "variant_sizes": variants,
                    "prices": {"Original": price_original, "Small": price_small, "Large": price_large}
                })
                collection.insert_one({
                    "painting_id": painting_id,
                    "image_hash": image_hash,
                    "title": title,
                    "size": size,
                    "medium": medium,
                    "description_lines": desc_lines,
                    "bullets": bullets,
                    "variant_sizes": variants,
                    "prices": st.session_state["prices"]
                })
            st.success("✅ New listing created!")

# Display Output
if "description_lines" in st.session_state:
    st.subheader("📄 Product Description")
    st.markdown(f"**Painting ID:** {st.session_state.get('painting_id', '')}")
    for line in st.session_state["description_lines"]:
        st.write(line)

if "bullets" in st.session_state:
    st.subheader("🔹 Amazon Bullet Points")
    st.markdown(st.session_state["bullets"])

# Export to PDF
if st.button("🧾 Export as A4 PDF"):
    if not all([price_original, price_small, price_large]):
        st.warning("Please enter all prices.")
    elif not all(k in st.session_state for k in ["description_lines", "bullets", "painting_id"]):
        st.warning("Generate listing before exporting.")
    else:
        pdf_path = generate_pdf(
            uploaded_file, title, medium,
            st.session_state["variant_sizes"],
            st.session_state["prices"],
            st.session_state["description_lines"],
            st.session_state["bullets"],
            st.session_state["painting_id"]
        )
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", data=f, file_name=f"{title}_listing.pdf", mime="application/pdf")

# Check MongoDB connection
try:
    client.admin.command('ping')
    st.success("Connected to MongoDB database.")
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")

# Check OpenAI API connection (compatible with openai>=1.0.0)
try:
    openai_client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    models = openai_client.models.list()
    st.success("Connected to OpenAI API.")
except Exception as e:
    st.error(f"Failed to connect to OpenAI API: {e}")

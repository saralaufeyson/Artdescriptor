# 🎨 AI Art Descriptor & PDF Generator 

A Streamlit web application that generates compelling descriptions for your artworks using OpenAI, and compiles them into a neat one-page PDF. It also stores artwork data in MongoDB to prevent redundant processing and enhance performance.

---

## ✨ Features

- 🧠 **AI-Powered Descriptions**: Automatically generate meaningful, elegant descriptions for your artworks using OpenAI's language model.
- 📄 **One-Page PDF Generation**: Export the artwork details along with its description into a single-page PDF.
- 🗃️ **MongoDB Integration**: Avoid repeat generation and save time with efficient artwork metadata storage.
- 🎨 **User-Friendly Interface**: Built with Streamlit for a simple and intuitive experience.

---

## 📦 Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI**: [OpenAI GPT API](https://platform.openai.com/)
- **Database**: [MongoDB](https://www.mongodb.com/)
- **PDF Creation**: `reportlab` / `fpdf` (or whichever library you used)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API Key
- MongoDB connection URI

### Installation

```bash
git clone https://github.com/yourusername/art-descriptor-app.git
cd art-descriptor-app
pip install -r requirements.txt
```
Environment Variables
Create a .env file in the project root and add the following:

```env

OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_uri
```
```Run the App

streamlit run app.py
```
###🧾 How It Works
Upload your artwork or enter artwork details.

The app checks MongoDB for existing entries based on the artwork's hash or title.

If it's a new entry, OpenAI generates a description.

A one-page PDF is created with all metadata and description.

The data is saved in MongoDB for future use.

###📌 To-Do / Future Enhancements
-🔍 Add image similarity matching to detect duplicates

-🖼️ Support for multiple artworks in batch

-☁️ Deploy on Streamlit Cloud or Hugging Face Spaces

-📧 Email the generated PDF to the user

##🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

##📜 License
This project is licensed under the MIT License


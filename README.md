# Artdescriptor

## Deploying to Streamlit Cloud

1. **Push your code to GitHub.**
2. **Go to [Streamlit Cloud](https://share.streamlit.io/)** and connect your GitHub repo.
3. **Set up secrets:**
   - In the Streamlit Cloud app dashboard, click on 'Edit Secrets'.
   - Add the following (replace with your actual keys):

```
OPENAI_API_KEY = "your-openai-key"
MONGO_URI = "your-mongodb-uri"
```

4. **Deploy the app.** Streamlit will automatically run `app.py`.

## Local Development

To run locally, create a `.streamlit/secrets.toml` file with:

```
OPENAI_API_KEY = "your-openai-key"
MONGO_URI = "your-mongodb-uri"
```

Then run:

```
streamlit run app.py
```

## Requirements

- Python 3.8+
- All dependencies in `requirements.txt`

---

For more info, see [Streamlit secrets documentation](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management).
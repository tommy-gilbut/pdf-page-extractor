FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit index.html에 Google Analytics 삽입
RUN GA_TAG='<script async src="https://www.googletagmanager.com/gtag/js?id=G-DY0E36RKW6"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag("js", new Date());\n  gtag("config", "G-DY0E36RKW6");\n</script>' && \
    INDEX=$(python -c "import streamlit, os; print(os.path.join(os.path.dirname(streamlit.__file__), 'static', 'index.html'))") && \
    sed -i "s|</head>|${GA_TAG}\n</head>|" "$INDEX"

COPY app.py .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false", "--server.maxUploadSize=512"]

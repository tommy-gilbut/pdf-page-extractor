FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit index.html에 Google Analytics 삽입
COPY ga.html /tmp/ga.html
RUN INDEX=$(python -c "import streamlit, os; print(os.path.join(os.path.dirname(streamlit.__file__), 'static', 'index.html'))") && \
    sed -i '/<\/head>/r /tmp/ga.html' "$INDEX" && \
    rm /tmp/ga.html

COPY app.py .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false", "--server.maxUploadSize=512"]

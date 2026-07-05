FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
# Ep buoc tai PyTorch ban CPU sieu nhe
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# Cai dat cac thu vien con lai
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

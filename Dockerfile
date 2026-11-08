# TacticLens app image, built from the Space folder (int8 ONNX model, no PyTorch).
#   python -m tacticlens.cli export-onnx && python -m tacticlens.cli bundle-space
#   docker build -t tacticlens .
#   docker run -p 7860:7860 tacticlens                          # web UI
#   docker run -p 8000:8000 tacticlens python api_server.py     # HTTP API (/docs)
FROM python:3.11-slim
WORKDIR /app
COPY space/ /app/
RUN pip install --no-cache-dir -r requirements.txt gradio fastapi uvicorn
EXPOSE 7860 8000
CMD ["python", "app.py"]

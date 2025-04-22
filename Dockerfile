# Use a lightweight Python base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all other files
COPY . .

# Set environment variables (these will be overridden by --env-file at runtime)
ENV HF_API_KEY=""
ENV PLOTLY_USERNAME=""
ENV PLOTLY_API_KEY=""

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]

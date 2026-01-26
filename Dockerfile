FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire project
COPY . /app/

# Expose Django port
EXPOSE 7000

# Auto run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:7000"]

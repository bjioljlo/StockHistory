# syntax=docker/dockerfile:1

FROM ubuntu:22.04 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python and basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies, including wget to download the TA-Lib source and Qt5 libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    wget \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5core5a \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Download, compile, and install the TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy and install Python dependencies
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Set Qt to use offscreen platform for headless operation
ENV QT_QPA_PLATFORM=offscreen

CMD ["python3", "-m", "src.main_stock"]

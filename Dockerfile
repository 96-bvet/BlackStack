FROM python:3.11-slim

# === System-level dependencies ===
RUN apt-get update && \
    apt-get install -y \
    libegl1 libgl1 libxkbcommon0 libdbus-1-3 \
    libxcb1 libxrender1 libxext6 libfontconfig1 libfreetype6 \
    libasound2 libportaudio2 ffmpeg \
    libopenblas0 libstdc++6 libgomp1 \
    python3-tk tk-dev libtk8.6 libtcl8.6 \
    libglib2.0-0 libx11-6 \
    && apt-get clean





# === Python dependencies ===
COPY requirements.txt /opt/wachter/
RUN pip install -r /opt/wachter/requirements.txt
RUN pip install PyQt6 PyQt6-Qt6 PyQt6-sip 
# === App setup ===
WORKDIR /opt/wachter
COPY . /opt/wachter
ENV WACHTER_HOME=/opt/wachter
CMD ["python3", "modules/gui/main_gui.py"]

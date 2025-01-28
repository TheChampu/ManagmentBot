FROM python:3.11.9

WORKDIR /root/Champubot

COPY . .

# Update package lists and install necessary packages
RUN apt-get update && apt-get install -y ffmpeg curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# Install Python dependencies
RUN pip install -U -r requirements.txt

CMD ["python3", "-m", "Champubot"]

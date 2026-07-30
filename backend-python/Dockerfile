FROM python:3.12-slim

ENV PIP_ROOT_USER_ACTION=ignore
ENV ISINCONTAINER=True

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN pip install --upgrade pip
# Install Kerberos build dependencies
RUN apt-get update && apt-get install -y \
    libkrb5-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    krb5-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD [ "python", "./Startup.py" ]
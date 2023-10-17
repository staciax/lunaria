FROM python:3.12-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install git to allow for the installation of private dependencies.
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

# Install the application's dependencies into the container.
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the source code into the container.
COPY . .

# Run the application.
CMD python launcher.py

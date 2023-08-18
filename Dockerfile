#######################
# Dockerfile
# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable for Flask to run in production mode
ENV FLASK_ENV=production

# Run the command to start the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "main:app"]
#=====================
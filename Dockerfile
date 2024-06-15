# Use the official Python image from the Docker Hub
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install the required packages
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port
EXPOSE 8051

# Command to run the app
CMD ["python", "app.py"]

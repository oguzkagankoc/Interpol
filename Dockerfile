# Set the base image to Python 3.8.16-buster
FROM python:3.8.16-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the container
COPY . .

# Run the database_creation.py script when the container starts
CMD python database_creation.py

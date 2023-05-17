FROM python:3.9

# Create the working directory
WORKDIR /app

# Copy the required packages
COPY requirements.txt .

# Install the packages
RUN pip install -r requirements.txt

# Copy the remaining files
COPY . .

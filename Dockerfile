# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install graphviz
RUN apt-get update && apt-get install -y graphviz

# Install uv
RUN pip install uv

# Copy the dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache .[dev]

# Copy the rest of the application's code
COPY ./app /app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

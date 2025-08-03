FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /code/app

# Set PYTHONPATH to ensure app module is found
ENV PYTHONPATH=/code

# Expose port
EXPOSE 80

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
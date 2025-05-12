# # Stage 1: Base build stage
# FROM python:3.13-slim AS builder
 
# # Create the app directory
# RUN mkdir /app
 
# # Set the working directory
# WORKDIR /app
 
# # Set environment variables to optimize Python
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1 
 
# # Upgrade pip and install dependencies
# RUN pip install --upgrade pip 
 
# # Copy the requirements file first (better caching)
# COPY requirements.txt /app/
 
# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt
 
# # Stage 2: Production stage
# FROM python:3.13-slim
 
# RUN useradd -m -r appuser && \
#    mkdir /app && \
#    chown -R appuser /app
 
# # Copy the Python dependencies from the builder stage
# COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
# COPY --from=builder /usr/local/bin/ /usr/local/bin/
 
# # Set the working directory
# WORKDIR /app
 
# # Copy application code
# COPY --chown=appuser:appuser . .
 
# # Set environment variables to optimize Python
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1 
 
# # Switch to non-root user
# USER appuser
 
# # Expose the application port
# EXPOSE 8000 


# RUN python manage.py collectstatic --noinput  # Collect static files during build
# # Start the application using Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "mysite.wsgi:application"]
# # CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# Stage 1: Base build stage
FROM python:3.13-slim AS builder
RUN mkdir /app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.13-slim
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
WORKDIR /app
COPY --chown=appuser:appuser . .
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
COPY nginx-render.conf /etc/nginx/conf.d/default.conf
RUN python manage.py collectstatic --noinput
CMD ["/bin/sh", "-c", "if [ \"$RENDER\" ]; then \
        python manage.py migrate --noinput && \
        nginx && gunicorn --bind 0.0.0.0:8000 --workers=2 --timeout=120 mysite.wsgi:application; \
    else \
        gunicorn --bind 0.0.0.0:8000 --workers=3 mysite.wsgi:application; \
    fi"]
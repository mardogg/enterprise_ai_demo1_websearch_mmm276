# Multi-stage build: build React app, then serve with Python
FROM node:20-alpine AS frontend-build

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Python runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python backend
COPY src/ ./src/
COPY .env.example ./.env

# Copy built React frontend
COPY --from=frontend-build /app/web/dist ./static

# Create a simple Flask server to serve the React app and provide API endpoints
COPY server.py ./

EXPOSE 8000

CMD ["python", "server.py"]

# Stage 1: Build React
FROM node:20-slim AS build-stage
WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ ./

# Debug: show files and try build with verbose error
RUN echo "=== FILES IN BUILD CONTEXT ===" && \
    ls -la src/ && \
    echo "=== NODE VERSION ===" && \
    node --version && \
    echo "=== ATTEMPTING BUILD ===" && \
    npx vite build 2>&1 || \
    (echo "=== BUILD FAILED - SHOWING DETAILED ERROR ===" && \
     node -e "import('vite').then(v=>v.build()).catch(e=>{console.error('ERROR TYPE:',e.constructor.name);console.error('MESSAGE:',e.message);if(e.cause)console.error('CAUSE:',e.cause);if(e.errors)e.errors.forEach((x,i)=>console.error('SUB-ERROR',i,':',x));process.exit(1)})" 2>&1 || \
     echo "=== FALLBACK: trying tsc ===" && \
     npx tsc --noEmit 2>&1; \
     exit 1)

# Stage 2: Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=build-stage /app/web/dist ./web/dist

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

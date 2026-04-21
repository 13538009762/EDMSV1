# Frontend Dockerfile - Multi-stage build
# Stage 1: Build
FROM node:20-alpine as build-stage

WORKDIR /app

# Set npm mirror for faster downloads
RUN npm config set registry https://registry.npmmirror.com

# Copy dependency files first to leverage Docker layer caching
COPY frontend/package*.json ./

# Install dependencies using clean install
# (Ensure package-lock.json is used for reproducible builds)
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine as production-stage

# Copy custom nginx config
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

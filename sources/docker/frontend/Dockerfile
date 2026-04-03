# Frontend Dockerfile - Multi-stage build
# Stage 1: Build
FROM node:20-alpine as build-stage

WORKDIR /app

# Copy all frontend source code
COPY frontend/ ./

# Install dependencies
RUN npm install

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

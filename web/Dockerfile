# Stage 1: Build React application
FROM node:20-alpine AS builder

WORKDIR /build

# Copy web package files (build context is repo root)
COPY web/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code (paths relative to repo root)
COPY web/src ./src
COPY web/public ./public
COPY web/tsconfig*.json web/vite.config.ts web/index.html ./

# Copy CHANGELOG from repo root for @repo/CHANGELOG.md?raw import
# Vite alias @repo resolves to repo root; CHANGELOG lands at /
COPY CHANGELOG.md ../

# Accept base path and Google OAuth client ID as build arguments
ARG VITE_BASE=/
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_BASE=$VITE_BASE
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# Build application (produces dist/)
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy nginx configuration
COPY web/nginx.conf /etc/nginx/nginx.conf

# Copy built application from stage 1
COPY --from=builder /build/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

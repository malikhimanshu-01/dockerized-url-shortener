# ---- build stage: compile the static bundle ----
# Also the image docker-compose.override.yml targets directly (`target: build`) to run
# `npm run dev` for hot reload — the HEALTHCHECK below is for that dev-mode use, since this
# stage's metadata doesn't carry into the "runtime" stage below (each FROM starts fresh).
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1:5173/ || exit 1

# ---- runtime stage: serve via nginx as a non-root user ----
FROM nginx:alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.d/10-generate-config.sh /docker-entrypoint.d/10-generate-config.sh

RUN chmod +x /docker-entrypoint.d/10-generate-config.sh \
    && chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD wget -qO- http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

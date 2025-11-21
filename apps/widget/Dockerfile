FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve with Nginx or similar for production, but for now we might just use a simple server or rely on GCS for the widget.
# For the Docker container in the compose file, we might want to run it in dev mode or serve the static files.
# Let's assume for the container we serve it.

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

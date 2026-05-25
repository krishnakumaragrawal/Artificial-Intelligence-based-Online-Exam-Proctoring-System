FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

FROM nginx:1.27-alpine

ENV API_BASE_URL=http://127.0.0.1:8000

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/10-write-config.sh /docker-entrypoint.d/10-write-config.sh
RUN chmod +x /docker-entrypoint.d/10-write-config.sh
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 5173

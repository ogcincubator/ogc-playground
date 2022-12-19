FROM node:lts-alpine AS builder

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY . .
RUN npm install && npm run build

FROM nginx:alpine as prod

ENV VUE_APP_BACKEND_URL http://backend:5000
ENV VUE_APP_SERVE_PATH /

WORKDIR /

COPY nginx.conf.tpl /etc/nginx/nginx.conf.tpl
COPY --from=builder /app/dist/ /app
COPY docker-entrypoint.sh /

EXPOSE 8080
ENTRYPOINT ["./docker-entrypoint.sh"]

FROM node:lts-alpine AS builder
ARG VUE_APP_BACKEND_URL=http://backend:5000

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH
ENV VUE_APP_BACKEND_URL $VUE_APP_BACKEND_URL

COPY . .
RUN npm install && npm run build

FROM nginx:alpine as prod

COPY nginx.conf /etc/nginx/nginx.conf
RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist/ /usr/share/nginx/html

EXPOSE 8080
ENTRYPOINT ["nginx", "-g", "daemon off;"]

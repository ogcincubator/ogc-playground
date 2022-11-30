FROM node:lts-alpine AS builder
ARG VUE_APP_BACKEND_URL=http://backend:5000
ARG VUE_APP_SERVE_PATH=/

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH
ENV VUE_APP_BACKEND_URL $VUE_APP_BACKEND_URL
ENV VUE_APP_SERVE_PATH ${VUE_APP_SERVE_PATH}

COPY . .
RUN npm install && npm run build

FROM nginx:alpine as prod
ARG VUE_APP_SERVE_PATH=/
ENV VUE_APP_SERVE_PATH ${VUE_APP_SERVE_PATH}

COPY nginx.conf.tpl /etc/nginx/nginx.conf.tpl
RUN envsubst '${VUE_APP_SERVE_PATH}' < /etc/nginx/nginx.conf.tpl > /etc/nginx/nginx.conf && \
    cat /etc/nginx/nginx.conf && \
    rm -rf /usr/share/nginx/html/* && \
    mkdir -p /usr/share/nginx/html/${VUE_APP_SERVE_PATH}

COPY --from=builder /app/dist/ /usr/share/nginx/html/${VUE_APP_SERVE_PATH}

EXPOSE 8080
ENTRYPOINT ["nginx", "-g", "daemon off;"]

#!/bin/sh

printenv | grep ^VUE_APP_ | while read APP_ENV_VAR; do
  NO_PREFIX=${APP_ENV_VAR/VUE_APP_/}
  VAR_NAME=${NO_PREFIX%%=*}
  VAR_VALUE=${APP_ENV_VAR#*=}
  sed -r "s@window.ogcPlayground.${VAR_NAME}.*@window.ogcPlayground.${VAR_NAME} = \"${VAR_VALUE}\";@" -i /app/env-config.js
done

sed -r 's@<base[^>]+>@@' -i /app/index.html
sed -r "s@<head>@<head><base href=\"${VUE_APP_SERVE_PATH}\">@" -i /app/index.html

envsubst '${VUE_APP_SERVE_PATH}' < /etc/nginx/nginx.conf.tpl > /etc/nginx/nginx.conf
rm -rf /usr/share/nginx/html/*
mkdir -p /usr/share/nginx/html${VUE_APP_SERVE_PATH}
cp -R /app/* /usr/share/nginx/html${VUE_APP_SERVE_PATH}

exec nginx -g "daemon off;"
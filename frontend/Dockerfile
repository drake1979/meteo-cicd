FROM nginx:1.23-alpine-slim
EXPOSE 80

RUN apk update && apk add dos2unix

WORKDIR /app
COPY build .
RUN chmod -R +r .

COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

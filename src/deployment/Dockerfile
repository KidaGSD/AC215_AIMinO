FROM nginx:stable-alpine

COPY nginx-conf/nginx/nginx.conf /etc/nginx/nginx.conf

COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

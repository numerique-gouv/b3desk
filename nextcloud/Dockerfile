FROM nextcloud:28.0.6

ARG WEBAPPPASSWORD_VERSION=24.4.0
ENV WEBAPPPASSWORD_VERSION=${WEBAPPPASSWORD_VERSION}

# cf https://github.com/nextcloud/docker/blob/master/24/apache/Dockerfile

# Install.
RUN apt update && apt install -y git wget

RUN sed -i 's/Listen 80/Listen 8000/' /etc/apache2/ports.conf && \
    sed -i 's/:80/:8000/' /etc/apache2/sites-available/000-default.conf

COPY ./apache2-sessiontoken /usr/bin/

# this WILL launch the /entrypoint.sh of the original dockerfile for Nextcloud.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-sessiontoken"]

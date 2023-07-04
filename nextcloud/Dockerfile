FROM nextcloud:25

# cf https://github.com/nextcloud/docker/blob/master/24/apache/Dockerfile

# Install.
RUN apt update && apt install -y git wget

COPY ./apache2-sessiontoken /usr/bin/

# this WILL launch the /entrypoint.sh of the original dockerfile for Nextcloud. 
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-sessiontoken"]

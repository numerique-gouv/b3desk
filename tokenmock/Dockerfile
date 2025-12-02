FROM python:3.14-slim

WORKDIR /opt/app

RUN apt update && apt install --yes curl
RUN pip install --no-cache-dir flask requests

# Copy application files
COPY app.py .
COPY healthcheck.sh .

RUN mkdir -p /opt/app/conf

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD ["./healthcheck.sh"]

CMD ["python", "app.py"]

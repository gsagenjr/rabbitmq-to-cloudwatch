# Pull consul-template from here
FROM hashicorp/consul-template:alpine

FROM alpine:3.7

#install prerequisites
RUN apk add -q --update --no-cache \
    python \
    py-pip \
    && pip install pyrabbit boto3

# Add base script
ADD rabbitmq-to-cloudwatch.py /rabbitmq-to-cloudwatch.py
CMD "chmod +x /rabbitmq-to-cloudwatch.py"

# Get consul-template
COPY --from=0 /bin/consul-template /
RUN chmod +x /consul-template

# Add and run the entrypoint script
ADD entrypoint.sh /
ENTRYPOINT ["./entrypoint.sh"]
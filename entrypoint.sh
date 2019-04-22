#!/bin/sh

# Get the config template from consul and render it
wget -O /application.ctmpl "http://$CONSUL_IP/v1/kv/rabbitmq-to-cloudwatch/application.ctmpl?raw"
./consul-template -consul-addr $CONSUL_IP -template "/application.ctmpl:/application.conf" -once

./rabbitmq-to-cloudwatch.py
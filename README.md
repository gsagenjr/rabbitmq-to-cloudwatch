#RabbitMQ-To-CloudWatch (With Consul-Template)

## Intro
This service is made to pull RabbitMQ queue sizes, and send them to AWS CloudWatch. This metric can then be used for alerts and as triggers for auto scaling.

This service is taken and tweaked from https://github.com/trailbehind/rabbitmq-to-cloudwatch

The goal of this fork is to add `consul-template` functionality (see https://github.com/hashicorp/consul-template), and generally make things more configurable, and broken down in to smaller functions with less parameters.

## Setup
Here are some of the commands I had to run to set up this services

```
pip install boto3 --user
pip install pyrabbit --user
```

## Config and Environment Parameters
Locally, the application can use `application.conf` in the same directory as the script. You can grab a copy of `application.conf.example` and save it as `application.conf` to run it locally.

From a docker container, it will pull from the application.ctmpl of the `$CONSUL_IP` environment variable and render it with the consul-template binary.

**It is important to note that  `aws_metric_name` should be set specific to the environment, so it doesnt overwrite another environments important metrics!**

You can set these environment parameters locally or on the docker container, and they will overwrite the config:
* **CONSUL_IP** - The ip address and port of the consul youd like to pull configs from
* **aws_metric_name** - The namespace that the metric will save under in cloudwatch. You need to set this per environment on the container, or it will save to the default in the config.
* aws_secret_key
* aws_access_key
* aws_region
* **sleep_interval_seconds** - Number of seconds in between each pull of the data from rabbit
* **rabbitmq_queue_names** - Set to plain queue names with spaces in between, for example: `exporter manager.links processing.audits`
* rabbitmq_host
* rabbitmq_user
* rabbitmq_password
* rabbitmq_vhost - Defaults to `\` or `%2f` in most rabbit setups
* rabbitmq_port

## Queues watched
You can changed the queues watched in the application.ctmpl. Just add the queue name you want to track.

Theres a commented line in the `get_queue_sizes` function that you should be able to use to grab ALL queues, instead of specifically named ones. I havent made it modular though, so its just commented out.

## Running locally
Run this command to run it locally:
```
python rabbitmq-to-cloudwatch.py 
```

To run with environment variables, you can do something like this:
```
export sleep_interval_seconds=30
export rabbitmq_queue_names='processing exporting emailing'
python rabbitmq-to-cloudwatch.py 
```

## Docker build and run
Run this from the project directory to build it, and then to run it with a consul_ip for locating the config.
```
docker build -t rabbitmq-to-cloudwatch:v1.<some version here> .
docker run -e CONSUL_IP=<ip here> rabbitmq-to-cloudwatch:v1.<some version here>
```

## Consul Keys and Templates
When running from docker, the config is pulled using a `wget` from `http://$CONSUL_IP/v1/kv/rabbitmq-to-cloudwatch/application.ctmpl?raw`, then rendered using `consul-template`. You can tweak this to whatever key you want to save the config under.

You can take a copy of `application.ctmpl.example` in consul at the key `rabbitmq-to-cloudwatch/application.ctmpl`, following its example for some hardcoded and some rendered keys.
#!/usr/bin/env python
from __future__ import with_statement, print_function

from pyrabbit.api import Client
import boto3
import os
import json
from time import sleep


# -------------- RabbitMQ --------------


def check_rabbit_connection(_rabbit_client):
    print("Checking if rabbit is alive")
    if not _rabbit_client.is_alive():
        raise Exception("Failed to connect to rabbitmq")
    print("Rabbit connection successful")


def get_rabbit_client(_host, _username, _password):
    return Client(_host, _username, _password)

def get_queue_sizes(_rabbit_client, _vhost, _queue_names):
    print("Making rabbit connection and checking if rabbit is alive")
    check_rabbit_connection(_rabbit_client)

    # This next comment is old code, so might not work, but with it you should be able to get ALL queues instead of just specified ones
    # _queue_names = [q['name'] for q in _rabbit_client.get_queues(vhost=_vhost)]
    queue_sizes = {}
    print("Getting queue sizes(depths in pyrabbit)")
    for queue in _queue_names:
        if queue == "aliveness-test":
            continue
        queue_sizes[queue] = _rabbit_client.get_queue_depth(_vhost, queue)
    return queue_sizes


# -------------- CloudWatch --------------

def get_cloudwatch_client(_region_name, _aws_access_key, _aws_secret_key):
    print("Setting up cloudwatch connection")
    # This is the JenkinsECS user
    return boto3.client('cloudwatch',
                        region_name=_region_name,
                        aws_access_key_id=_aws_access_key,
                        aws_secret_access_key=_aws_secret_key)

def publish_individual_queue_size_to_cloudwatch(_cloudwatch_client, _queue_name, _queue_size, _metric_name):
    print("Putting metric namespace=%s name=%s unit=Count value=%i" %
          (_metric_name, _queue_name, _queue_size))

    _cloudwatch_client.put_metric_data(
        MetricData=[
            {
                'MetricName': _queue_name,
                'Unit': 'Count',
                'Value': _queue_size
            },
        ],
        Namespace=_metric_name
    )

def publish_queue_sizes_to_cloudwatch(_cloudwatch_client, _queue_sizes, _metric_name):
    print("Publishing queue sizes to cloudwatch")
    for queue in _queue_sizes:
        publish_individual_queue_size_to_cloudwatch(_cloudwatch_client, queue, _queue_sizes[queue], _metric_name)



# -------------- Main --------------

if __name__ == "__main__":
    print("Getting config")
    with open('application.conf') as json_config:
        config = json.load(json_config)


    print("Config found. Using environmental variables first, config second if no environmental variables are found.")
    rabbit_host = os.environ.get("rabbitmq_host", config['rabbitmq']['host']+':'+config['rabbitmq']['port'])
    rabbit_username = os.environ.get("rabbitmq_user", config['rabbitmq']['username'])
    rabbit_password = os.environ.get("rabbitmq_password", config['rabbitmq']['password'])
    rabbit_vhost = os.environ.get("rabbitmq_vhost", config['rabbitmq']['vhost'])
    rabbit_port = os.environ.get("rabbitmq_port", config['rabbitmq']['port'])
    rabbit_queue_names = os.environ.get("rabbitmq_queue_names", config['rabbitmq']['queue_names'])

    sleep_interval_seconds = float(os.environ.get("sleep_interval_seconds", config['sleep_interval_seconds']))

    aws_secret_key = os.environ.get("aws_secret_key", config['aws']['secret_key'])
    aws_access_key = os.environ.get("aws_access_key", config['aws']['access_key'])
    aws_region = os.environ.get("aws_region", config['aws']['region'])
    aws_metric_name = os.environ.get("aws_metric_name", config['aws']['metric_name'])

    print("Done pulling settings")

    print("Tracking queues: ", rabbit_queue_names)
    if isinstance(rabbit_queue_names, str):
        rabbit_queue_names = rabbit_queue_names.split (' ')

    print("Getting rabbit client connection")
    rabbit_client = get_rabbit_client(rabbit_host, rabbit_username, rabbit_password)
    check_rabbit_connection(rabbit_client)

    print("Getting cloudwatch client connection")
    cloudwatch_client = get_cloudwatch_client(aws_region, aws_access_key, aws_secret_key)

    print("Publishing metrics every %s seconds" % sleep_interval_seconds)

    # Main service loop
    while True:
        queue_sizes = get_queue_sizes(rabbit_client, rabbit_vhost, rabbit_queue_names)

        publish_queue_sizes_to_cloudwatch(cloudwatch_client, queue_sizes, aws_metric_name)

        print("Sleeping")
        sleep(sleep_interval_seconds)
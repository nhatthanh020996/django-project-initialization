import logging
import json
from datetime import datetime
from typing import Optional, Callable
import uuid
import uuid
import time

import pika
from pika.exceptions import AMQPChannelError, AMQPConnectionError
from pika.adapters.blocking_connection import BlockingChannel
from pika import BasicProperties

from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)

class RabbitMQWrapper():
    def __init__(
        self, 
        host: str = None, 
        port: int = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        client_properties: Optional[dict] = None
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._client_properties = client_properties
        self._connection = self._create_connection()
        self._channel = self.connection.channel()

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    @property
    def client_properties(self):
        return self._client_properties

    @client_properties.setter
    def client_properties(self, value):
        self._client_properties = value

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value


    def _create_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        conn_params = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials,
                                                client_properties=self.client_properties,)
        
        connection = pika.BlockingConnection(conn_params)
        return connection
    
    def reconnect(self):
        self.connection = self._create_connection()
        self.channel = self.connection.channel()

    def create_queue(self, queue):
        return self.channel.queue_declare(queue=queue, durable=True)

    def create_exchange(self, name: str, type: str):
        return self.channel.exchange_declare(exchange=name, exchange_type=type)
    
    def bind_queue(self, exchange: str, queue: str, binding_key: str):
        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=binding_key)
    
    def consume(self, queue: str, callback: Callable):
        self.channel.basic_consume(queue=queue, on_message_callback=callback)

    def start_consuming(self):
        self.channel.start_consuming()

    def close(self):
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def publish_message(self, routing_key, exchange, data, message_id=None, props={}):
        if message_id is None:
             message_id = str(uuid.uuid4())
        properties=pika.BasicProperties(content_type='application/json', delivery_mode=2,
                                        timestamp=int(time.time()),
                                        message_id=message_id,
                                        **props)
        
        self.channel.basic_publish(exchange=exchange, routing_key=routing_key, properties=properties,
                                   body=data)


class AMQPBaseCallback:
    enable_check_auth = False

    def __init__(self, ch: BlockingChannel, method, properties: BasicProperties, json_body):
        self._ch = ch
        self._method = method
        self._properties = properties
        self._json_body = json_body
        
        self.message = None
        self.message_id = None
        self.merchant = None

        self._error = None
        self.callback()
    
    def __enter__(self):
        pass

    def __exit__(self):
        pass
    
    def callback(self):
        """
        """
        try:
            self.initialize()
            response = self.handle_message()

        except Exception as exc:
            response = None
            self.handle_exception(exc)
        self.finalize(response)

    def authenticate(self):
        pass

    def initialize(self, **kwargs):
        self.message = json.loads(self._json_body)
        self.message_id = self._properties.message_id

        extra = {
            'message_id': self.message_id,
            'routing_key': self._method.routing_key,
            'message_body': self.message,
            'message_props': self._properties.__dict__
        }
        logger.info('Incomming Message', extra=extra)

        if self.enable_check_auth:
            self.authenticate()

    def handle_message(self):
        raise NotImplementedError(
            'subclasses of AMQPConsumeBaseCommand must provide a handle_message() method'
        )

    def handle_exception(self, exc):
        """
        """
        self._error = exc
        extra = {'message_body': self.message, 'message_id': self.message_id, 'message_props': self._properties.__dict__}
        logger.exception('An Exception Occurs', extra=extra)

    def finalize(self, response, *args, **kwargs):
        """
        If there is no error, send ack to the queue. Otherwise, sending nack to the queue
        """
        delivery_tag = self._method.delivery_tag
        if self._error is not None:
            return self._ch.basic_nack(delivery_tag, multiple=True, requeue=False)
        return self._ch.basic_ack(delivery_tag, multiple=True)


class AMQPConsumeBaseCommand(BaseCommand):
    """
    This class is designed to be a base class for consuming message from a particular 
    queue. Other classes that inherit from this one have to declare properties like:
    `host`, `post`, `credential`, `exchange`, `exchange_type`, `queue_name`, and `binding_keys`.
    Note that, we just have a channel and a comsumer that is created from the channel. So
    if you want to have many channels or many comsumers. This class is not suitable for
    for purpose.
    """
    client_properties = None
    host = None
    port = None
    username = None
    password = None
    credential = None

    exchange = None
    exchange_type = None
    queue_name = None
    binding_key = None
    consumer_tag = None

    prefetch_count = 10

    message_retries = {}
    max_retries = 3


    callback = AMQPBaseCallback

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conn_params = pika.ConnectionParameters(host=self.host, port=self.port,
                                                      credentials=pika.PlainCredentials(self.username, self.password),
                                                      client_properties=self.client_properties)

        self._connection: pika.BlockingConnection = pika.BlockingConnection(self._conn_params)
        self._channel: BlockingChannel = self._connection.channel()
        self._stop_consuming = False

    def recreate_connection(self):
        """
        Creating a new connection and assigning it to self._connection
        """
        assert self._connection.is_closed, (
            'Cannot create a new connection when the previous one is alive'
        )
        self._connection = pika.BlockingConnection(self._conn_params)

    def recreate_channel(self):
        """
        Creating a new channel and assigning it to self._channel
        """
        assert self._connection.is_open, (
            "Create a new connection before creating a channel"
        )
        if self._connection.is_closed:
            self._connection = pika.BlockingConnection(self._conn_params)
        self._channel = self._connection.channel()


    def init_queue(self):
        self._channel.queue_declare(self.queue_name, durable=True)
        self._channel.queue_bind(exchange=self.exchange, queue=self.queue_name,
                                    routing_key=self.binding_key)
        return self._channel

    def init_exchange(self):
        self._channel.exchange_declare(self.exchange, self.exchange_type, durable=True)

    def start_consume(self):
        with self._channel:
            self._channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback,
                                        consumer_tag=self.consumer_tag)
            self._channel.start_consuming()

    def handle_amqp_conn_error(self, error):
        if self._connection.is_open:
            self._connection.close()
        logger.exception('AMQP connection error', extra={'details': str(error)})
        self.recreate_connection()
        self.recreate_channel()

    def handle_amqp_channel_error(self, error):
        logger.exception('AMQP channel error', extra={'details': str(error)})
        if self._channel.is_open:
            self._channel.stop_consuming()
            self._channel.close()
        self.recreate_channel()

    def run(self, **options):
        """
        """
        self.init_exchange()
        self.init_queue()
        now = datetime.now().strftime('%B %d, %Y - %X')
        self.stdout.write(now)
        self.stdout.write((
            "Starting consumer to subscribe RabbitMQ server at: "
            "%(host)s:%(port)s with queue_name = %(queue)s, "
            "exchange = %(exchange)s"
        ) % {
            "host": self.host,
            "port": self.port,
            "queue": self.queue_name,
            "exchange": self.exchange
        })

        while not self._stop_consuming:
            try:
                self._channel.basic_qos(prefetch_count=self.prefetch_count)
                self.start_consume()
            except AMQPConnectionError as e:
                self.handle_amqp_conn_error(e)
            except AMQPChannelError as e:
                self.handle_amqp_channel_error(e)
            except KeyboardInterrupt:
                self._channel.stop_consuming()
                self._connection.close()
                self._stop_consuming = True # not try to consume again.
            except Exception as e:
                logger.exception('Unexpected Error from RabbitMQ')

    def handle(self, *args, **options):
        """
        """
        self.run(**options)

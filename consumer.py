import pika
from multiprocessing import Process
from app import application
from database_operations import DatabaseOperationsCallback
import os
from dotenv import load_dotenv
load_dotenv()
# Access variables
rabbitmq_host = os.getenv('RABBITMQ_HOST')
# Define a class to consume messages from a RabbitMQ queue
class RabbitMQConsumer:
    def __init__(self):

        # Create a connection to the local RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        self.channel = self.connection.channel()

        # Declare queues to consume messages from
        self.channel.queue_declare(queue='add_data')
        self.channel.queue_declare(queue='change_data')

        # Set up consumers to consume messages from the queue and call the callback function for each message
        self.channel.basic_consume(queue='add_data', on_message_callback=self.callback, auto_ack=True)
        self.channel.basic_consume(queue='change_data', on_message_callback=self.callback_change, auto_ack=True)

    # Define callback functions to be called for each message consumed from the queue
    def callback_change(self, ch, method, properties, body):

        # Print the message received from the queue
        print(" [x] Received %r" % body.decode('utf-8'))

        # Process the message body by passing it to the DatabaseOperationsCallback class
        operator = DatabaseOperationsCallback(body)
        operator.callback_change_db()

    def callback(self, ch, method, properties, body):
        # Print the message received from the queue
        print(" [x] Received %r" % body.decode('utf-8'))

        # Process the message body by passing it to the DatabaseOperationsCallback class
        operator = DatabaseOperationsCallback(body)
        operator.callback_db()

    def start_consuming(self):
        # Start consuming messages from the queue
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def close(self):
        # Close the RabbitMQ connection
        self.connection.close()


# Define a consumer function that initializes and starts a RabbitMQ consumer
def consumer():
    consumer = RabbitMQConsumer()
    consumer.start_consuming()


# Check if the current script is being run as the main entry point
if __name__ == "__main__":
    # Create two Process objects, each associated with a target function
    process1 = Process(target=consumer)
    process2 = Process(target=application)

    # Start the processes, which will execute the target functions concurrently
    process1.start()
    process2.start()

    # Wait for the processes to finish their execution
    process1.join()
    process2.join()


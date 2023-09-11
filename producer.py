import pika

import json

from utils import setup_log
from connect_db import connector, fill_data, choose_db
from fill_db import seed

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials))
channel = connection.channel()

channel.exchange_declare(exchange='mail_push', exchange_type='direct')
channel.queue_declare(queue='mail_queue', durable=True)
channel.queue_bind(exchange='mail_push', queue='mail_queue')

def change_bool(customer_data):
    reader = choose_db('newsletter')
    update = {'$set': {'check': True}}
    reader.update_many(customer_data, update)

def main(data: list[dict]):
    for customer in data:
        customer_without_id = {key: value for key, value in customer.items() if key != '_id'}
        channel.basic_publish(
            exchange='mail_push',
            routing_key='mail_queue',
            body=json.dumps(customer_without_id).encode(),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))
        change_bool(customer_without_id)
        print(" [x] Sent %r" % customer_without_id['name'])

        
    connection.close()
    

if __name__ == '__main__':
    setup_log()
    connector()
    for _ in range(30):
        data = seed()
        fill_data(data, 'rabbitmq')
    
    reader = choose_db('newsletter')
    result = reader.find()
    list_of_results = [ r for r in result]

    main(list_of_results)
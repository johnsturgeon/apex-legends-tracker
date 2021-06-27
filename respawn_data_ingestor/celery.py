""" Celery app start up script """
from celery import Celery

app = Celery('respawn_data_ingestor',
             broker='amqp://',
             backend='rpc://',
             include=['respawn_data_ingestor.ingestion_tasks'])


if __name__ == '__main__':
    app.start()

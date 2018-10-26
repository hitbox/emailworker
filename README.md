# emailworker

Python 3 email sending worker using pika and RabbitMQ. Minimal email worker for
my own needs.

## Application Configuration
If it exists, application configuration is pulled from `./instance/config.py`

`cp config/config.bare.py instance/`

Edit for your needs.

## RabbitMQ Configuration

`cp config/rabbitmq.bare.ini instance/rabbitmq.ini`

Edit for your needs.

## Test email

`cp config/email.bare.ini instance/testemail.ini`

Edit with your data.

To send a test email to workers:

`python -m emailworker send`

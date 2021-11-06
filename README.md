# telegram-bell


![PyPI](https://img.shields.io/pypi/v/telegram-bell)

Notify you when something is mentioned in a telegram channel.

## Install

    pip install telegram-bell

## Usage

### CLI

#### Run


    tbell run

Before you can use, it will ask you for:

- your Telegram API ID
- your Telegram API hash
- channels and keywords which you want to get notified
- Telegram token (2FA)

Then, the app will resend you the coinciding messages to your 'Saved Messages' channel in Telegram.

#### Config

    tbell config


#### Show susbscribed channels

    tbell show

### Systemd user service

Clone the repo and:

    cd telegram-bell/scripts
    sh install_service.sh
    sh start_service.sh # it will ask you for config

Check the service is running:

    sh check_service.sh

You can check the services logs too:

    sh show_service_logs.sh


If the service fails or the machine is restarted, the service will run transparently again.

If you want to change your config in some moment:

    tbell config
    sh restart_service.sh
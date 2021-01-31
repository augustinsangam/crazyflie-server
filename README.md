# Server

Server connected to drones and dashboard

## Getting started

Please follow steps below to launch the server.

```bash
# Install python env
sudo apt-get install python-is-python3 python3-venv

# Create environment
python3 -m venv .venv

# Activate the environment
. ./.venv/bin/activate

# Update pip just in case
pip install -U pip

# Install wheel package
pip install wheel

# Install dependencies
pip install -r requirements.txt

# Start app in dev mode
python3 server.py

# Start app in production mode
# uwsgi --ini=wsgi.ini
```

## Others scripts

```bash
# Extract dependencies
>requirements.txt pip freeze

# Update dependencies 
mv requirements.txt requirements.txt.orig
<requirements.txt.orig >requirements.txt sed 's/==/>=/g'
rm requirements.txt.orig
pip install -U -r requirements.txt
>requirements.txt pip freeze
```
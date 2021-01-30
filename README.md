# server

Server connected to drones and dashboard

TODO: multi-threaded bjoern

INSTALL UWSGI BINARY AND UWSGI PYTHON3 MODULE FROM YOUR DISTRO

### CREATE PYTHON ENVIRONMENT ###
python3 -m venv .venv

### ACTIVATE ENVIRONMENT ###
. ./.venv/bin/activate

### UPDATE PIP JUST IN CASE ###
pip install -U pip

### INSTALL WHEEL PACKAGE
pip install wheel

### INSTALL DEPENDENCIES ###
pip install -r requirements.txt

### START APP IN DEVELOPMENT MODE ###
python3 app.py

### START APP IN PRODUCTION MODE ###
uwsgi --ini=wsgi.ini

### DEACTIVATE ENVIRONMENT ###
deactivate

### EXTRACT DEPENDENCIES ###
>requirements.txt pip freeze

### UPDATE DEPENDENCIES ###
mv requirements.txt requirements.txt.orig
<requirements.txt.orig >requirements.txt sed 's/==/>=/g'
rm requirements.txt.orig
pip install -U -r requirements.txt
>requirements.txt pip freeze

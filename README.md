# Server

This repository stores the code of the master-server, which links the dashboard to the ARGoS3 drones or the real drones.

## Getting started

Please follow steps below to launch the server.

```sh
# Install python env
sudo apt-get install python3-venv uwsgi-plugin-python3

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
python src/server.py

# Start app in production mode
# uwsgi --ini=wsgi.ini
```

## Others scripts

```sh
# Deactivate environment
deactivate

# Extract dependencies
>requirements.txt pip freeze

# Update dependencies 
mv requirements.txt requirements.txt.orig
<requirements.txt.orig >requirements.txt sed 's/==/>=/g'
rm requirements.txt.orig
pip install -U -r requirements.txt
>requirements.txt pip freeze
```

## Docker
```bash
# build
docker build -t crazyflie-server .
# run
docker run -it --name crazyflie-server -p 3995:3995 -p 5000:5000 crazyflie-server
```

## Documentation generation
To generate the project's documentation :

* Install Doxygen
  ```bash
  git clone https://github.com/doxygen/doxygen.git
  cd doxygen
  mkdir build && cd build
  cmake -G "Unix Makefiles" ..
  make
  make install
  ```
* Once in a while, run Doxygen. Make sure you are in the root directory of the project (`/server`)
  ```bash
  doxygen doc/doxygen-config
  ```

  The output can be found in the `latex` folders located in `doc`.
  
  To generate a PDF :
  ```bash
  cd doc/latex
  make pdf
  ```

Example of a docstring :
```python
def exitHandler(signal, frame):
    """Function description

        @param signal: signal parameter description
        @param frame: frame parameter description
    """
    import logging
    logging.info('CLOSING SERVER APPLICATION')
    pass
```

FROM python:3.8

WORKDIR /code

COPY ./src .

# Copy the requirements file
COPY requirements.txt ./

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt


# Create environment
RUN python3 -m venv .venv

# Activate the environment
RUN . ./.venv/bin/activate

# Install wheel and uwsgi package
RUN pip install wheel uwsgi

#CMD [ "uwsgi", "--ini=wsgi.ini" ]

CMD [ "python", "./server.py" ]




FROM python:3.8.2

ARG SETTINGS_MODULE=mas_problem.settings.prod_settings

EXPOSE 8000

WORKDIR /app

COPY requirements.txt /app/

RUN ["pip", "install", "-r", "requirements.txt"]
RUN ["pip", "install", "daphne"]

COPY . /app/

# TODO: change to prod_settings after test
ENV DJANGO_SETTINGS_MODULE=$SETTINGS_MODULE

RUN ["python", "manage.py", "migrate"]

RUN ["python", "manage.py", "collectstatic", "--noinput"]

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "mas_problem.asgi:application"]

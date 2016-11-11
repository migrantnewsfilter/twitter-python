FROM python:2-onbuild

ADD . /twitter

RUN pip install -r /twitter/requirements.txt

WORKDIR /twitter

CMD [ "python", "-u", "__main__.py" ]

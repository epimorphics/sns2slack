FROM public.ecr.aws/lambda/python:3.8

RUN mkdir -p /libs

COPY sns2slack.py ./
COPY requirements.txt ./

RUN python -m pip install --upgrade pip
RUN python${RUNTIME_VERSION} -m pip install -r requirements.txt --target /libs
ENV PYTHONPATH=/libs

CMD ["sns2slack.handler"]

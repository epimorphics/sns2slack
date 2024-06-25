ARG PYTHON_VERSION
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

RUN mkdir -p /libs

COPY sns2slack.py ./
COPY requirements.txt ./

RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt --target /libs
ENV PYTHONPATH=/libs

CMD ["sns2slack.handler"]

FROM python:3.6.4

RUN python3 -m pip install spacy==2.0.11 -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN python3 -m spacy download en

FROM gmirror/geek-digest-nlp:latest

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo "Asia/Shanghai" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak && \
    echo "deb http://mirrors.ustc.edu.cn/debian jessie main non-free contrib" >/etc/apt/sources.list && \
    echo "deb http://mirrors.ustc.edu.cn/debian jessie-proposed-updates main non-free contrib" >>/etc/apt/sources.list && \
    echo "deb-src http://mirrors.ustc.edu.cn/debian jessie main non-free contrib" >>/etc/apt/sources.list && \
    echo "deb-src http://mirrors.ustc.edu.cn/debian jessie-proposed-updates main non-free contrib" >>/etc/apt/sources.list
RUN apt update

RUN apt install vim -y

WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

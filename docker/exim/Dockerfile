FROM debian:stretch-slim
RUN apt update
COPY debconf /exim4-debconf
RUN debconf-set-selections /exim4-debconf
RUN apt install -y exim4
ENTRYPOINT /usr/sbin/exim -bd -v
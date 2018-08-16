FROM centos:7
MAINTAINER Maojingjing


RUN mkdir /rqalpha

COPY ./ /rqalpha/


EXPOSE 8080
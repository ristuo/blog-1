FROM wordpress
RUN apt-get update -yqq &&\
  apt-get install -yqq vim htop zip devscripts fakeroot build-essential dh-apache2
COPY libs/apache2-mod-log-ipmask-master.zip /apache2-mod-log-ipmask-master.zip
RUN cd / && unzip apache2-mod-log-ipmask-master.zip
RUN cd /apache2-mod-log-ipmask-master &&\
  dpkg-buildpackage -uc -us &&\
  dpkg -i ../libapache2-mod-log-ipmask_1.0.0_amd64.deb &&\ 
  a2enmod log_ipmask
COPY log_ipmask.conf /etc/apache2/mods-available/log_ipmask.conf
RUN a2enmod ssl
RUN a2ensite default-ssl.conf
COPY default-ssl.conf /etc/apache2/sites-available
COPY 000-default.conf /etc/apache2/sites-available

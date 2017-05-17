# Named Entity Tagging #
[TOC]

# Overview #
Named entity tagging using dictionaries

# Development #
## Using [python virtual environment](http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/) ##
### Command line ###
```
#!bash
pip install virtualenv
cd path/to/project
virtualenv worker
./worker/bin/python main.py
```
### IDE (e.g PyCharm) ###
[Creating Virtual Environment](https://www.jetbrains.com/help/pycharm/2017.1/creating-virtual-environment.html)
## Using docker ##
```
#!bash
cd /path/to/project (e.g cd /root/projects/named-entity-tagging)
docker-compose up
```
# Testing #

* Web UI: http://localhost:1999

* API Swagger: http://localhost:1999/doc

* Unit test: must have Elasticsearch run on local by `docker-compose up elasticsearch`, modify `util/database.py` to change `elasticsearch:900` to `localhost:9200`
```
#!bash
./worker/bin/python tests/test.py
```
# Deployment #
Current deployed branch: `optimize_english`

Using `docker-compose up` to run application.
```
#!bash
git clone https://bitbucket.org/diepdt/named-entity-tagging.git
git fetch && git checkout optimize_english
cd named-entity-tagging
docker-compose up
```
Using [**supervisor**](https://www.digitalocean.com/community/tutorials/how-to-install-and-manage-supervisor-on-ubuntu-and-debian-vps) to monitor application processes, it will **automatically restart** application when **crash** or **server reboot**.
```
#!bash
sudo supervisorctl

supervisor> status
cerebro                          RUNNING   pid 29112, uptime 0:38:45
ner                              RUNNING   pid 31649, uptime 0:09:15

supervisor> restart ner
ner: stopped
ner: started

supervisor> tail -f ner
```
There 2 running apps

* [ner](http://138.68.14.35:1999/): Named entity tagging application and APIs
* [cerebro](http://138.68.14.35:9000/#/overview?host=http:%2F%2F138.68.14.35:9200): Monitor Elasticsearch cluster 

View logs
```
#!bash
tail -f /var/log/ner.out.log
```

Supervisor config:

* ner: `cat /etc/supervisor/conf.d/ner.conf`
```
#!bash
[program:ner]
command=docker-compose up
directory=/root/projects/named-entity-tagging
autostart=true
autorestart=true
stdout_logfile=/var/log/ner.out.log
redirect_stderr=true
```
* cerebro: `cat /etc/supervisor/conf.d/cerebro.conf`

```
#!bash
[program:cerebro]
environment=JAVA_HOME=/root/java/jre1.8.0_131
command=/root/cerebro-0.6.5/bin/cerebro
directory=/root/cerebro-0.6.5
autostart=true
autorestart=true
stdout_logfile=/var/log/cerebro.out.log
redirect_stderr=true
```

# Authors #

* Diep Dao - diepdaocs@gmail.com
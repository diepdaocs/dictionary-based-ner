### Named Entity Tagging ###

Named entity tagging using dictionaries

### Development ###
Using docker
```
#!bash
cd /path/to/project (e.g cd /root/projects/named-entity-tagging)
docker-compose up
```

### Deployment ###
Using `docker-compose up` to run application.

Using **supervisor** to monitor application processes, it will **automatically restart** application when **crash** or **server reboot**.
```
#!bash
sudo supervisorctl

supervisor> status
cerebro                          RUNNING   pid 29112, uptime 0:38:45
ner                              RUNNING   pid 31649, uptime 0:09:15

supervisor> restart ner
ner: stopped
ner: started

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

### Authors ###

* Diep Dao - diepdaocs@gmail.com
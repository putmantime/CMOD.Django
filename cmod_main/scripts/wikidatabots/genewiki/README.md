genewiki
========

The GeneWiki Project

### Overview
The code in this repo handles the automated updates of gene templates, and as well as the on-request article creation requests from the BioGPS plugin (http://biogps.org/genewikigenerator/).  Both types of edits are made under the ProteinBoxBot Wikipedia account.

### Project Setup

#### Server Dependencies

* `sudo apt-get update`
* `sudo apt-get upgrade`
* `sudo apt-get install build-essential python3 python-dev python-pip python-virtualenv libmysqlclient-dev git-core nginx supervisor rabbitmq-server graphviz libgraphviz-dev pkg-config libncurses5-dev`
*  mwclient not compatiable with python3 must change code errors.py client.py (check for upgrades to the package first)

* `mkdir webapps`
* `cd webapps`
* `git clone https://sulab@bitbucket.org/sulab/wikidatabots.git`
* `cd wikidatabots/genewiki`
* `git fetch --all`
* `git reset --hard origin/master`


#### virtualenv

A Python Virtual Environment is used to ensure that the application runs in an isolated and protected environment

* Create a new virtual environment: `sudo virtualenv -p /usr/bin/python3.4 /opt/genewiki-venv3`
* Activate the environment `source /opt/genewiki-venv3/bin/activate`

If you see `(genewiki-venv3)` in front of your shell, this worked.

* `sudo /opt/genewiki-venv3/bin/pip install -r requirements.txt`
*  copy python modules 
	 `cp wikidatabots/PBB_Core/*py /opt/genewiki-venv3/lib/python3.4/site-packages/`


#### Setup

The `config` directory in this project hosts template files and their location for nginx, gunicorn and supervisor
* Supervisor : Copy config/*.conf into /etc/supervisor/conf.d (must update permissions on conf.d)
* nginx : Copy config/default into /etc/nginx/conf.d (upd perm on conf.d to allow copy)
* copy config/gunicorn_start into /bin


#### Configuration

The settings files are not included in the repo for security reasons and must be uploaded to the server.
*cp settings.py file to wikidatabots/genewiki/genewiki/

* `sudo adduser deploy`

* `sudo /etc/init.d/nginx restart`
* `cd /home/ubuntu/webapps/genewiki/ & mkdir logs`

* `sudo supervisorctl reread`
* `sudo supervisorctl add genewiki`
* `sudo supervisorctl add genewiki_celery`

* `touch debug.log`
* `chmod 777 debug.log`

* `sudo chown deploy:deploy /bin/gunicorn_start`
* `sudo chmod a+x /bin/gunicorn_start`

* `sudo chmod 777 webapps/genewiki/logs/`
* `import os`
`os.environ['DJANGO_SETTINGS_MODULE'] = 'genewiki.settings'`
* 'python manage.py syncdb'
*  `python manage.py collectstatic`
#### Application

* `sudo supervisorctl restart genewiki_celery`
* `sudo supervisorctl restart genewiki`


### Utils

* Flow diagram of the database relationships
* `python manage.py graph_models -a -o myapp_models.png`
* `celery --app=genewiki.common worker -B -E -l INFO`
* `ssh -i .ssh/path/to/key ubuntu@suv05.scripps.edu`


### Notes



### Known issues:


### Definitions:



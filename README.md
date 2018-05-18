# WARNING
公开此代码作为交流学习的用途。因为经过修改后并没有测试因此并不保证此代码能够正常运行。

Public this Repository just for Learning and Communicating.Don't ensure this Repository code can work ,because it edit from personal Repository and don't really run this code before.

#seafile-OA

base on seafile,fit with seafile 6.1.1,a app of seahub django project.


# develop

* `setenv.sh` to prepare environment.

* `export WEB_DEVELOP=True` to set DEBUG=True, other will be False.


# deploy

1. backup origin file, cover origin file with soft link file under seafile-server-laster/seahub folder.

    `cd /path/to/seafile-server-latest/seahub/`

    `ln -s /path/to/seafile-OA/office ./`

    `mv manage.py manage.py.bak`

    `mv seahub/wsgi.py seahub/wsgi.py.bak`

    `rm seahub/wsgi.pyc`

    `ln -s /path/to/seafile-OA/manage.py ./`

    `ln -s /path/to/seafile-OA/seahub/wsgi.py seahub/`

    copy setenv.sh from this repo and edit it.

2. set env and be ready for django and database.

    (edit django_constance-1.0.1-py2.6.egg/constance/models.py)

    `. setenv.sh`

    `python manage.py collectstatic`

    `python manage.py migrate contenttypes --fake`

    `python manage.py migrate auth`

    `python manage.py migrate admin`

    `python manage.py migrate office`

3. use `seafile-server-laster/seahub.sh start` to start seahub.

# clean blockhole with crontab

`cp clean_blockhole.sh.tmp clean_blockhole.sh`

`chmod +x clean_blockhole.sh`

edit clean_blockhole.sh for right path

`crontab -e`

# Upgrade Seafile server

1. Upgrade seafile.

2. rebuild this repo. step base on the point 1 of deploy. 

3. `python manage.py collectstatic`

4. edit the files of `custom/templates` for the last version seafile.


# don't support

 * seafile use LDAP user
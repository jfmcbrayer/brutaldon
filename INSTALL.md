Installing brutaldon
====================

Brutaldon is a perfectly normal Django app, so if you've ever installed a Django app, it should be straightforward. It will work either as a local application, or installed on a server.

For either case, you will need Python 3 installed to start with, including pip.

Common steps
---------------------------------------------------------
If you haven't already, you need to install [Pipenv][pe], a tool for managing Python virtual environments. 

You can install it just with  `pip install pipenv`.

[pe]: https://github.com/pypa/pipenv/

Development or local install
------------------------------------------------
In the top brutaldon directory, run `pipenv install`. This will install all the dependencies. Then run `pipenv run python ./manage.py migrate`. That will create a SQLite database the application needs. Then run `pipenv run python ./manage.py runserver`. That will start a local server on http://localhost:8000/.

Point your browser to that address and log in to your instance. You will have to log in with the alternate (username and password) method. 

Server installation
----------------------------------------
This will depend on your server setup, and you should consult [Deploying Django][dd]. Be sure to read the [Deployment checklist][dc], because some things in it are security critical. You will also want to set up a database. Brutaldon doesn't use the database very heavily, so if you only have a few users, the default SQLite is probably fine and doesn't require any additional setup.

One common step would be to install dependencies like this: `PIPENV_VENV_IN_PROJECT=1 pipenv install`. This will install dependencies within the project folder. 

Then edit brutaldon/settings.py. You definitely need to change the values of SECRET_KEY and ALLOWED_HOSTS. Also edit the database parameters to match the database you chose. Then run `pipenv run python ./manage.py migrate` to populate the database.

I installed brutaldon with Apache and mod_wsgi. If you installed brutaldon in /usr/local/share/, you'd add config lines something like this to the virtual host brutaldon is installed in.

```
Alias /brutaldon/static /usr/local/share/brutaldon/brutaldon/static
<Directory /usr/local/share/brutaldon/brutaldon/static>
    Require all granted
</Directory>

WSGIScriptAlias /brutaldon /usr/local/share/brutaldon/brutaldon/wsgi.py
WSGIDaemonProcess brutaldon python-path=/usr/local/share/brutaldon python-home=/usr/local/share/brutaldon/.venv

<Directory /usr/local/share/brutaldon/brutaldon>
    <Files wsgi.py>
    Require all granted                                                    
    </Files>
</Directory>
```

Be sure you serve the entire site over https only.

[dd]: https://docs.djangoproject.com/en/2.0/howto/deployment/
[dc]: https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

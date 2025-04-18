# What is this?
The web server code and webpage templates for
[my blog](https://blog.matthewrease.net).
## Why?
My old system, though neat in its own right, especially for something I came up
with around 2019/2020 when I had little to no experience in such things, had
many drawbacks, and overall just didn't seem to be made the way real web
applications are made. Also I can show this to a job recruiter. :)
## Where's the data?
See the sister project `blog-posts` under this same user account (not linked
for... reasons).

# Running This App
For the best experience please pass `--ini default.ini` to `uwsgi`. You may
overwrite values at your discretion, but the logging it setup in a specific way,
so that the Python app can determine which posts are accessed the most.
## Needed Libraries
Package names according to PyPI:
- Markdown
- mysqlclient
- dotenv
- Flask
- pillow
## Environment Variables
Create a .env file, or manually set the following environment variables:
- `MYSQL_USER`: authenticating username
- `MYSQL_PASSWORD`: authenticating password
- `MYSQL_DATABASE`: the database on `localhost` to use
- `USE_CSP`: either `true` or `false` depending on whether you want to enable Content Security Policy
## Production vs Testing?
My test environment isn't too dissimilar from the real one, I just use 'blog'
for all 3 .env variables. The main difference is how I run it (technically). On
my Arch laptop I run:
```
uwsgi --plugin python --http :5000 --wsgi-file app.py
```

But on my server I have to say python3, and also the version seems different so
the args change a bit to http-socket. Additionally I add --master:
```
uwsgi --plugin python3 --http-socket :5000 --wsgi-file --master app.py
```

SimpleLogin - privacy-first email alias and Single Sign-On (SSO) Identity Provider
---

https://simplelogin.io

> Yet another email forwarding service?

In some way yes ... However SimpleLogin is a bit different because:

- it's fully open-source: both the server and client code (browser extension, JS library) are open-source so anyone can freely inspect and (hopefully) improve the code.
- not just email alias: SimpleLogin is a privacy-first and developer-friendly identity provider that: a. offers privacy for users b. is simple to use for developers. Our goal is to offer a privacy-focused alternative to the "Login with Facebook/Google/Twitter" buttons.
- the only email alias solution that is `self-hostable`: with our detailed self-hosting instructions and most of components running as Docker container, anyone who knows how to `ssh` is able to deploy SimpleLogin on their server.  
- plenty of features: custom domain, browser extension, alias activity, OAuth libraries, etc.
- written in Python 🐍 😅 this is not a difference per se but hey I never found a Python email server so feel free to tweak this one if you want to use Python for handling emails.

# Table of Contents

[1. General Architecture](#general-architecture)

[2. Self Hosting](#self-hosting)

[3. Contributing Guide](#contributing)


## General Architecture

![](docs/archi.png)

SimpleLogin backend consists of 2 main components: 

- the `webapp` used by several clients: web UI (the dashboard), browser extension (Chrome & Firefox for now), OAuth clients (apps that integrate "Login with SimpleLogin" button) and mobile app (work in progress).

- the `email handler`: implements the email forwarding (i.e. alias receiveing email) and email sending (i.e. alias sending email). 

## Self hosting

### Prerequisites

- a Linux server (either a VM or dedicated server). This doc shows the setup for Ubuntu 18.04 LTS but the steps could be adapted for other popular Linux distributions. As most of components run as Docker container and Docker can be a bit heavy, having at least 2 GB of RAM is recommended. The server needs to have the port 25 (email), 80, 443 (for the webapp), 22 (so you can ssh into it) open.

- a domain that you can config the DNS. It could be a subdomain. In the rest of the doc, let's say it's `mydomain.com` for the email and `app.mydomain.com` for SimpleLogin webapp. Please make sure to replace these values by your domain name whenever they appear in the doc.

- [Optional]: a dedicated Postgres database. If you don't want to manage and maintain a Postgres database, you can use managed services proposed by some cloud providers. Otherwise this guide will show how to run a Postgres database using Docker. Database is not well-known to be run inside Docker but this is probably fine if you don't have thousands of email addresses.

- [Optional] AWS S3, Sentry, Google/Facebook/Github developer accounts. These are necessary only if you want to activate these options.

All the below steps, except for the DNS ones that are usually done inside your domain registrar interface, are done on your server. The commands are to run with `bash` (or any bash-compatible shell like `zsh`) being the shell. If you use other shells like `fish`, please make sure to adapt the commands.

### DKIM

From Wikipedia https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail

> DomainKeys Identified Mail (DKIM) is an email authentication method designed to detect forged sender addresses in emails (email spoofing), a technique often used in phishing and email spam.

Setting up DKIM is highly recommended to reduce the chance your emails ending up in the recipient's Spam folder.

First you need to generate a private and public key for DKIM:

```bash
openssl genrsa -out dkim.key 1024
openssl rsa -in dkim.key -pubout -out dkim.pub.key
```

You will need the files `dkim.key` and `dkim.pub.key` for the next steps.

For email gurus, we have chosen 1024 key length instead of 2048 for DNS simplicity as some registrars don't play well with long TXT record.

### DNS

Please note that DNS changes could take up to 24 hours to propagate. In practice, it's a lot faster though (~1 minute or so in our test).

#### MX record
Create a **MX record** that points `mydomain.com` to `app.mydomain.com` with priority 10.

To verify if the DNS works, `dig mydomain.com mx` should contain the following in the result. 

```
mydomain.com.	3600	IN	MX	10 app.mydomain.com.
```

#### A record
An **A record** that points `app.mydomain.com` to your server IP. To verify, `dig app.mydomain.com a` should return your server IP.

#### DKIM
Set up DKIM by adding a TXT record for `dkim._domainkey.mydomain.com` with the following value:

```
v=DKIM1; k=rsa; p=PUBLIC_KEY
```

with `PUBLIC_KEY` being your `dkim.pub.key` but
- remove the `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----`
- join all the lines on a single line.

For example, if your `dkim.pub.key` is 

```
-----BEGIN PUBLIC KEY-----
ab
cd
ef
gh
-----END PUBLIC KEY-----
```

then the `PUBLIC_KEY` would be `abcdefgh`.

To verify, `dig dkim._domainkey.mydomain.com txt` should return the above value.

#### SPF

From Wikipedia https://en.wikipedia.org/wiki/Sender_Policy_Framework

> Sender Policy Framework (SPF) is an email authentication method designed to detect forging sender addresses during the delivery of the email

Similar to DKIM, setting up SPF is highly recommended. 
Add a TXT record for `mydomain.com` with the value `v=spf1 mx -all`. What it means is only your server can send email with `@mydomain.com` domain. To verify, you can use `dig mydomain.com txt`

#### DMARC (optional) TODO

### Docker

Now the boring DNS stuffs are done, let's do something more fun!

Please follow the steps on [Docker CE for Ubuntu](https://docs.docker.com/v17.12/install/linux/docker-ce/ubuntu/) to install Docker on the server. 

Tips: if you want to run Docker without the `sudo` prefix, add your account to `docker` group:

```bash
sudo usermod -a -G docker $USER
```

### Prepare the Docker network

This Docker network will be used by the other Docker containers run in the next steps.
Later, we will setup Postfix to authorize this network.

```bash
docker network create -d bridge \
    --subnet=1.1.1.0/24 \
    --gateway=1.1.1.1 \
    sl-network
```

### Postgres

This sections show how to run a Postgres database using Docker. At the end of this section, you will have a database username and password that're going to be used in the next steps.

If you already have a Postgres database, you can skip this section and just copy the database configuration (host, port, username, password, database name).

Run a postgres Docker container. Make sure to replace `myuser` and `mypassword` by something more secret 😎.

```bash
docker run -d \
    --name sl-db \
    -e POSTGRES_PASSWORD=mypassword \
    -e POSTGRES_USER=myuser \
    -e POSTGRES_DB=simplelogin \
    --network="sl-network" \
    postgres
```

To test if the database runs correctly, run

```bash
docker exec -it sl-db psql -U myuser simplelogin
```

you should be logged into postgres console.

### Postfix

Install `postfix` and `postfix-pgsql`. The latter is used to connect Postfix and Postgres database in the next steps.

```bash
sudo apt-get install -y postfix postfix-pgsql
```

Choose "Internet Site" in Postfix installation window then keep using the proposed value as *System mail name* in the next window. 

Run the following commands to setup Postfix. Make sure to replace `mydomain.com` by your domain.

```bash
sudo postconf -e 'myhostname = app.mydomain.com'
sudo postconf -e 'mydomain = mydomain.com'
sudo postconf -e 'myorigin = mydomain.com'
sudo postconf -e 'mydestination = localhost'

sudo postconf -e 'mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128 1.1.1.0/24'

sudo postconf -e 'relay_domains = pgsql:/etc/postfix/pgsql-relay-domains.cf'
sudo postconf -e 'transport_maps = pgsql:/etc/postfix/pgsql-transport-maps.cf'
```


Create the `relay-domains` file at `/etc/postfix/pgsql-relay-domains.cf` and put the following content. Make sure that the database config is correctly set and replace `mydomain.com` by your domain.

```
# postgres config
hosts = localhost
user = myuser
password = mypassword
dbname = simplelogin

query = SELECT domain FROM custom_domain WHERE domain='%s' AND verified=true UNION SELECT '%s' WHERE '%s' = 'mydomain.com' LIMIT 1;
```

Create the `transport-maps` file at `/etc/postfix/pgsql-transport-maps.cf` and put the following lines. Make sure that the database config is correctly set and replace `mydomain.com` by your domain.

```
# postgres config
hosts = localhost
user = myuser
password = mypassword
dbname = simplelogin

# forward to smtp:127.0.0.1:20381 for custom domain AND email domain
query = SELECT 'smtp:127.0.0.1:20381' FROM custom_domain WHERE domain = '%s' AND verified=true UNION SELECT 'smtp:127.0.0.1:20381' WHERE '%s' = 'mydomain.com' LIMIT 1;
```

Finally restart Postfix

> sudo systemctl restart postfix

### Run SimpleLogin Docker containers

To run the server, you need a config file. Please have a look at [config example](./.env.example) for an example to create one. Some parameters are optional and are commented out by default. Some have "dummy" values, fill them up if you want to enable these features (Paddle, AWS). 

Let's put your config file at `~/simplelogin.env`.

Make sure to update the following variables

```.env
# Server url
URL=http://app.mydomain.com
EMAIL_DOMAIN=mydomain.com
SUPPORT_EMAIL=support@mydomain.com
EMAIL_SERVERS_WITH_PRIORITY=[(10, "app.mydomain.com.")]
DKIM_PRIVATE_KEY_PATH=/dkim.key

# optional, to have more choices for random alias.
WORDS_FILE_PATH=local_data/words_alpha.txt
```


Before running the webapp, you need to prepare the database by running the migration

```bash
docker run \
    --name sl-migration \
    -v $(pwd)/dkim.key:/dkim.key \
    -v $(pwd)/simplelogin.env:/code/.env \
    --network="sl-network" \
    simplelogin/app flask db upgrade
```

This command could take a while to download the `simplelogin/app` docker image.

Now it's time to run the `webapp` container!

```bash
docker run -d \
    --name sl-app \
    -v $(pwd)/simplelogin.env:/code/.env \
    -v $(pwd)/dkim.key:/dkim.key \
    -p 7777:7777 \
    --network="sl-network" \
    simplelogin/app
```

Next run the `email handler`

```bash
docker run -d \
    --name sl-email \
    -v $(pwd)/simplelogin.env:/code/.env \
    -v $(pwd)/dkim.key:/dkim.key \
    -p 20381:20381 \
    --network="sl-network" \
    simplelogin/app python email_handler.py
```

[Optional] If you want to run the cronjob:

```bash
docker run -d \
    --name sl-cron \
    -v $(pwd)/simplelogin.env:/code/.env \
    -v $(pwd)/dkim.key:/dkim.key \
    --network="sl-network" \
    simplelogin/app yacron -c /code/crontab.yml
```

### Nginx

Install Nginx

```bash
sudo apt-get install -y nginx
```

Then create `/etc/nginx/sites-enabled/simplelogin` with the following lines:

```
server {
    server_name  app.mydomain.com;

    location / {
        proxy_pass http://localhost:7777;
    }
}
```

Reload nginx with 

```bash
sudo systemctl reload nginx
```

At this step, you should also setup the SSL for Nginx. [Certbot](https://certbot.eff.org/lets-encrypt/ubuntuxenial-nginx) can be a good option if you want a free SSL certificate.

### Enjoy!

If all the steps are successful, open http://app.mydomain.com/ and create your first account! 

## Contributing

All work on SimpleLogin happens directly on GitHub. 

### Run code locally

The project uses Python 3.6+. First, install all dependencies by running the following command. Feel free to use `virtualenv` or similar tools to isolate development environment.

```bash
pip3 install -r requirements.txt
```

Then make sure all tests pass

```bash
pytest
```

To run the code locally, please create a local setting file based on `.env.example`:

```
cp .env.example .env
```

Make sure to uncomment the `RESET_DB=true` to create the database locally.

Feel free to custom your `.env` file, it would be your default setting when developing locally. This file is ignored by git.

You don't need all the parameters, for ex if you don't update images to s3, then
`BUCKET`, `AWS_ACCESS_KEY_ID` can be empty or if you don't use login with Github locally, `GITHUB_CLIENT_ID` doesn't have to be filled. The `.env.example` file contains minimal requirement so that if you run:

```
python3 server.py
```

then open http://localhost:7777, you should be able to login with the following account

```
john@wick.com / password
```

### API

For now the only API client is the Chrome/Firefox extension. This extension relies on `API Code` for authentication. 

In every request the extension sends

- the `API Code` is set in `Authentication` header. The check is done via the `verify_api_key` wrapper, implemented in `app/api/base.py`

- the current website `hostname` which is the website subdomain name + domain name. For ex, if user is on `http://dashboard.example.com/path1/path2?query`, the subdomain is `dashboard.example.com`. This information is important to know where an alias is used in order to proposer to user the same alias if they want to create on alias on the same website in the future. The `hostname` is passed in the request query `?hostname=`, see `app/api/views/alias_options.py` for an example.

Currently the latest extension uses 2 endpoints:

- `/alias/options`: that returns what to suggest to user when they open the extension. 

```
GET /alias/options hostname?="www.groupon.com"

Response: a json with following structure. ? means optional field.
	recommendation?:
		alias: www_groupon_com@simplelogin.co
		hostname: www.groupon.com

	custom: 
		suggestion: groupon
		suffix: [@my_domain.com, .abcde@simplelogin.co]

	can_create_custom: true

	existing:
		[email1, email2, ...]
```

- `/alias/custom/new`: allows user to create a new custom alias.

```
POST /alias/custom/new
	prefix: www_groupon_com
	suffix: @my_domain.com

Response:
	201 -> OK {alias: "www_groupon_com@my_domain.com"}
	409 -> duplicated

```

### Database migration

The database migration is handled by `alembic`

Whenever the model changes, a new migration needs to be created

Set the database connection to use a current database (i.e. the one without the model changes you just made), for ex if you have a staging config at `~/config/simplelogin/staging.env`, you can do: 

> ln -sf ~/config/simplelogin/staging.env .env

Generate the migration script and make sure to review it before commit it. Sometimes (very rarely though), the migration generation can go wrong.

> flask db migrate

### Code structure

The repo consists of 3 entry points:

- wsgi.py and server.py: the webapp. 
- email_handler.py: the email handler. 
- cron.py: the cronjob. 

Here are a small sum-ups of the directory structure and their roles:

- app/: main Flask app. It is divided into different packages that represents different features like oauth,  api, dashboard, etc.
- local_data/: contain files that are there to facilitate local development. They are replaced during the deployment.
- migrations/: generated by flask-migrate. Edit these files only when you spot (very rare) errors on database migration files.
- static/: files available at `/static` url. 
- templates/: contain both html and email templates.
- tests/: tests. We don't really distinguish unit, functional or integration test. A test is simply here to make sure a feature works correctly.

The code is formatted using https://github.com/psf/black, to format the code, simply run

```
black
```

### OAuth flow

SL currently supports code and implicit flow.

#### Code flow

To trigger the code flow locally, you can go to the following url after running `python server.py`:  

```
http://localhost:7777/oauth/authorize?client_id=client-id&state=123456&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A7000%2Fcallback&state=random_string
```

You should see there the authorization page where user is asked for permission to share their data. Once user approves, user is redirected to this url with an `authorization code`: `http://localhost:7000/callback?state=123456&code=the_code`

Next, exchange the code to get the token with `{code}` replaced by the code obtained in previous step. The `http` tool used here is https://httpie.org

```
http -f -a client-id:client-secret http://localhost:7777/oauth/token grant_type=authorization_code code={code}
```

This should return an `access token` that allow to get user info via the following command. Again, `http` tool is used.

```
http http://localhost:7777/oauth/user_info 'Authorization:Bearer {token}'
```

#### Implicit flow

Similar to code flow, except we get the `access token` back with the redirection. 
For implicit flow, the url is 

```
http://localhost:7777/oauth/authorize?client_id=client-id&state=123456&response_type=token&redirect_uri=http%3A%2F%2Flocalhost%3A7000%2Fcallback&state=random_string
```

#### OpenID, OAuth2 response_type & scope

According to https://medium.com/@darutk/diagrams-of-all-the-openid-connect-flows-6968e3990660

- `response_type` can be either `code, token, id_token`  or any combination.
- `scope` can contain `openid` or not

Below is the different combinations that are taken into account in SL until now:

```
response_type=code
    scope:
	    with `openid` in scope, return `id_token` at /token: OK
	    without: OK

response_type=token
    scope:
	    with and without `openid`, nothing to do: OK

response_type=id_token
    return `id_token` in /authorization endpoint
    
response_type=id_token token
    return `id_token` in addition to `access_token` in /authorization endpoint
   
response_type=id_token code
    return `id_token` in addition to `authorization_code` in /authorization endpoint

```






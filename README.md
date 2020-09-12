# ![Logo](https://i.imgur.com/l1yzk4N.png) GRUA (Generic Resources Unifier and Allocator)
![License](https://img.shields.io/badge/license-Apache%202-blue.svg)

GRUA is a *[Puppet External Node Classifier (ENC)][ENC]* application. Here are some of its key features:

- **Multi-tenant support:** It is possible to manage multiple Puppet Servers (called Master Zones) with a single GRUA application;
- **Multi-environments support:** GRUA supports multiple Puppet Servers environments and it can automatically sync information about them; 
- **Access control:** It is possible to establish selective restrictions of access to Master Zone, depending on the user permissions. Also, GRUA's API is protected and requires authentication; 
- **Group-orientation**: Nodes can only be associated to groups. And groups are abstractions that are associated with a Puppet Server and one of its environments, that may contain classes and parameters.

## Tech

GRUA uses the following technologies:

- **Database:** *[PostgreSQL 9.6.9][POSTGRESQL]*
- **Backend:** *[Python 3.6][PYTHON]* + *[Django 2][DJANGO]* + *[Django Rest][DJANGO_REST]*;
- **Frontend:** *[HTML5][HTML5]* + *[Sass][SASS]* + *[JS][JS]* (*[ES6][ES6]* + *[Babel][BABEL]*) + *[Gulp][GULP]*.
- **Docker image:** *[postgres][POSTGRES_DOCKER]* + *[contribsys/faktory][FAKTORY_DOCKER]* + *[python:3-alpine][PYTHON_DOCKER]*

## How to run (with Docker)

GRUA is very easy to install and deploy in Docker containers, through Docker Compose.

Set environment variables on `docker-compose.yml` on `scheduler` and `worker` services:
```yaml
  ...
  scheduler:
    ...
    environment:
      - WEBAPP_USER=<username to be created>
      - WEBAPP_PASS=<user pass to be created>
  ... 
  worker:
    ...
    environment:
      - WEBAPP_USER=<username to be created>
      - WEBAPP_PASS=<user pass to be created>
  ...
```

Build the containers with:
```bash
docker-compose build
```

Apply database migrations with:
```bash
docker-compose run webapp python manage.py migrate
```

Create an admin user with the information provided in `WEBAPP_USER` and `WEBAPP_PASS`:
```bash
docker-compose run webapp python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('<chosen username>', '<user email>', '<chosen password>')"
```

Spin up the containers with:
```bash
docker-compose up
```

By default, the Docker will expose port 8080.
Therefore, you can access the main webapp at *[localhost:8000][GRUA_URL]*.

## Usage and documentation

A more complete documentation of GRUA can be found on our *[wiki][WIKI]*.

### Setting up a Puppet Server to communicate with GRUA

In order to a Puppet Server correctly communicate with GRUA there are two viable options:

1. Use our *[puppet-grua module][MODULE]* on each Puppet Server on your infrastructure that should be communicating with GRUA;
2. Manually perform the following actions:
   1. Create a Master Zone for the Puppet Server: ![Creating a Master Zone](https://i.imgur.com/vLyKAwk.gif)
   2. Obtain the Master Zone id (UUID) via GRUA's API (on *[/api/master_zones][MASTER_ZONES_URL]*): ![Obtaining Master Zone's UUID](https://i.imgur.com/iEtSqQb.gif)
   3. Access the Puppet Server responsible for the Puppet CA;
   4. Generate a certificate for GRUA via Puppet CA;
   5. Sign this certificate via Puppet CA;
   6. Create/obtain a token on GRUA's admin page for an admin user (on *[/admin/authtoken/token/add/][TOKEN_URL]*): ![Creating a new GRUA auth token](https://i.imgur.com/rKJ4fki.gif)
   7. Config Puppet Server's API permissions to allow requests with the generated certificate on the classes/environments endpoints (using Master Zone's UUID value and GRUA's auth token);
   8. Restart the Puppet Server;
   9. Upload the certificate file and the key file for the PuppetServer (Master Zone) via a PUT on GRUA API (on *[/api/master_zones/<master_zone_id>][MASTER_ZONE_PUT_URL]*): ![Uploagind Master Zone's certificate files](https://i.imgur.com/39HYlqd.gif)
   10. Create a file on the Puppet Server to consult GRUA's API node_classifier endpoint (on *[/api/nodes/node_classifier/?certname=<node_certname>&master_id=<master_zone_id>][NODE_CLASSIFIER_URL]*); 
   11. Restart the Puppet Server
   12. Repeat steps 9, 10 and 11 for each compiler on a non-monolithic server architecture.

We absolutely recommend you to choose the first option, as it is much easier and the straight-forward one to go with.


### API

Our API is documented using *[Swagger][SWAGGER]* and can be accessed on GRUA via *[/docs/ URL path][DOCS_URL]*.

### Release History

- 0.1.0
  - Public release
- 0.1.1
  - Fix node-sass version on package.json
  - Update info about environment variables `WEBAPP_USER` and `WEBAPP_PASS`


## Meta

Distributed under the Apache 2 license. See *[LICENSE][LICENCE]* for more information.

### Author

- Oscar Esgalha (oscar at instruct dot com dot br)

### Contributors

- Aurora Wang (aurora dot wang at instruct dot com dot br);
- Dirceu Silva (dirceu dot silva at instruct dot com dot br);
- Fabio Iassia (fabio at instruct dot com dot br);
- Joao Nascimento (joao dot nascimento at instruct dot com dot br);
- João Sizílio (joao dot sizílio at instruct dot com dot br);
- Luana Lima (luana dot lima at instruct dot com dot br);
- Thiago Pena (thiagopena at instruct dot com dot br);
- Jeferson Costa (jeferson dot costa at instruct dot com dot br);

[ENC]: https://puppet.com/docs/puppet/5.5/nodes_external.html
[WIKI]: https://github.com/instruct-br/grua/wiki
[MODULE]: https://github.com/instruct-br/puppet-grua/
[MASTER_ZONES_URL]: http://localhost:8000/api/master_zones/
[TOKEN_URL]: http://localhost:8000/admin/authtoken/token/add/
[MASTER_ZONE_PUT_URL]: http://localhost:8000/api/master_zones/<master_zone_id>/
[NODE_CLASSIFIER_URL]: http://localhost:8000/api/nodes/node_classifier/?certname=<node_certname>&master_id=<master_zone_id>
[POSTGRESQL]: https://www.postgresql.org/
[PYTHON]: https://www.python.org/download/releases/3.0/
[DJANGO]: https://docs.djangoproject.com/en/2.1/releases/2.0/
[DJANGO_REST]: https://www.django-rest-framework.org/
[HTML5]: https://www.w3.org/TR/html5/
[SASS]: https://sass-lang.com/
[JS]: https://www.javascript.com/
[ES6]: http://es6-features.org/
[BABEL]: https://babeljs.io/
[GULP]: https://gulpjs.com/
[POSTGRES_DOCKER]: https://hub.docker.com/_/postgres/
[FAKTORY_DOCKER]: https://hub.docker.com/r/contribsys/faktory/
[PYTHON_DOCKER]: https://hub.docker.com/_/python/
[GRUA_URL]: http://localhost:8000/
[SWAGGER]: https://swagger.io/
[DOCS_URL]: http://localhost:8000/docs/
[LICENCE]: https://github.com/instruct-br/grua/blob/master/LICENSE

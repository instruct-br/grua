The `puppet/v3/environment_classes` endpoint in a PuppetServer requires
authenticated requests. This repository have some dummy certs for testing
purposes.

In production the worker config at `docker-compose.yml` should look like this:
```
version: '2'

services:
  worker:
    volumes:
      - /etc/puppetlabs/puppet/ssl/:/certs
    environment:
      - CERT_NAME=puppet-grua.example.com.pem
```

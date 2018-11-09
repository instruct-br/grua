# Contributing guidelines 

Want to contribute? Awesome!

## Contribution steps

1. First and foremost: adhere to our *[Code of Conduct][CODE_OF_CONDUCT]*;
2. Fork it (https://github.com/instruct-br/grua/fork);
2. Create your feature branch (git checkout -b feature/fooBar);
3. Commit your changes with an *[informative message][COMMIT]* (git commit);
4. Push to the branch (git push origin feature/fooBar);
5. Create a new Pull Request following the project's pull request template (available on Github interface).

## Development environment (with Docker)

GRUA has a `docker-compose.dev.yml` file specifically created to help the development process.
It is responsible to mount volumes on Docker so the changes you made on the code are reflected on the containers.

Build the containers with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
```

Apply database migrations with:
```bash
docker-compose run webapp python manage.py migrate
```

Create a generic admin user:
```bash
docker-compose run webapp python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
```

Spin up the containers with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Frontend static assets are mapped with local files in the development containers.
To generate assets locally you need to install JS dependencies: *[npm 6.4.1][NPM]* and *[node v8.12.0][NODE]*.
These assets can be created with:
```bash
cd webapp/
npm install
npm run build
cd ..
```

## Style guide

We mostly use *[PEP8][PEP8]* as our style guide (aside of us allowing bigger line lengths).

You can use *[Black][BLACK]* to format your code (while the containers are up):
```bash
docker exec -it grua_webapp_1 black .
```

And *[Flake8][FLAKE8]* to check it  (while the containers are up):
```bash
docker exec -it grua_webapp_1  pipenv run flake8 --exclude=*/migrations/* --exclude node_modules/ --ignore=E501 .
```

## Tests

We also encourage developers to implement tests when contributing to a new feature or a bug fix.
It is possible to run tests with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml run webapp python manage.py test
```

[CODE_OF_CONDUCT]: https://github.com/instruct-br/grua/blob/master/CODE_OF_CONDUCT.md
[NPM]: https://www.npmjs.com/
[NODE]: https://nodejs.org/en/
[COMMIT]: https://chris.beams.io/posts/git-commit/
[FLAKE8]: http://flake8.pycqa.org/en/latest/
[BLACK]: https://github.com/ambv/black
[PEP8]: https://www.python.org/dev/peps/pep-0008/

PROJECT = socialnetwork
SERVICE = web
DB = pg
DC = docker-compose -p $(PROJECT)
SRC = src
PYTEST = pytest -v --log-level=INFO

up:
	$(DC) up -d --build

help:
	@echo "  up         docker-compose build and up"
	@echo "  restart    docker-compose restart"
	@echo "  ps         docker-compose ps"
	@echo "  bash       application bash"
	@echo "  log        application log"
	@echo "  bash-pg    postgresql bash"
	@echo "  test       run test"
	@echo "  check      check code"
	@echo "  format     format code"
	@echo "  clean      clean dev staff"

build:
	$(DC) build
stop:
	$(DC) stop
down:
	$(DC) down --rmi local --remove-orphans
build-no-cache:
	$(DC) build --no-cache
restart: stop down build up
	@echo "docker-compose has ben restarted!"
ps:
	$(DC) ps
bash:
	$(DC) exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" $(SERVICE) /bin/sh
log:
	$(DC) logs -f $(SERVICE)
attach:
	docker attach $(PROJECT)_$(SERVICE)_1

bash-pg:
	$(DC) exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" $(DB) /bin/sh
psql:
	$(DC) exec $(DB) psql pythons -h localhost -U monty
psql-log:
	$(DC) logs -f $(DB)

test:
	$(DC) exec $(SERVICE) $(PYTEST) $(SRC)/tests
black:
	$(DC) exec $(SERVICE) black --diff --config black.toml $(SRC)
flake8:
	$(DC) exec $(SERVICE) flake8 --config setup.cfg $(SRC)
pylint:
	$(DC) exec $(SERVICE) pylint --rcfile setup.cfg $(SRC)

black-format:
	$(DC) exec $(SERVICE) black --config black.toml $(SRC)
autopep8-format:
	$(DC) exec $(SERVICE) autopep8 --verbose --recursive --in-place -a -a $(SRC)
isort-format:
	$(DC) exec $(SERVICE) isort --recursive $(SRC)
autoflake-format:
	$(DC) exec $(SERVICE) autoflake --recursive --in-place --remove-unused-variables --remove-all-unused-imports $(SRC)

cov cover coverage:
	$(DC) exec $(SERVICE) pytest -s --cov $(SRC) --cov-report html $(SRC)/tests && exit
	@echo "open file://`pwd`/htmlcov/index.html"
	eval "open file://`pwd`/htmlcov/index.html"

mypy:
	$(DC) exec $(SERVICE) /bin/sh -c "cd src/ && mypy --config-file ../mypy.ini main.py bg_tasks db web"

hadolint:
	docker run --rm -i hadolint/hadolint < Dockerfile

format: autoflake-format isort-format autopep8-format black-format
	@echo "Apply autoflake-format isort-format autopep8-format black-format!"

check: black flake8 pylint mypy hadolint cov
	@echo "Run black flake8 pylint mypy hadolint cov!"

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf htmlcov
	rm -rf dist

.PHONY: all up build stop down build-no-cache restart ps bash log attach bash-pg psql-log adev black flake8 pylint black-format autopep8-format isort-forma cov cover coverage check format hadolint clean autoflake-format

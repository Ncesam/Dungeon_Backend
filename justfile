
alias sda := start-dev-api
alias sa := start-api
alias i := install

# Run Dev Mode API
start-dev-api:
    docker-compose -f docker/compose/base.yaml -f docker/compose/dev.yaml up --build

# Run Prod Mode API
start-api:
    docker-compose -f docker/compose/base.yaml -f docker/compose/prod.yaml up --build

# Install all dependencies
install:
    poetry install -n --no-root





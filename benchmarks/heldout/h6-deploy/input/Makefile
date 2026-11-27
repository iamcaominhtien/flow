REGISTRY ?= registry.example.com/shop
TAG ?= dev

lint:
	ruff check .

test:
	pytest -q

image:
	docker build -t $(REGISTRY)/api:$(TAG) .

push:
	docker push $(REGISTRY)/api:$(TAG)

deploy:
	./scripts/deploy.sh $(ENV) $(TAG)

smoke:
	./scripts/smoke.sh $(ENV)

rollback:
	./scripts/deploy.sh $(ENV) $$(cat .last_good_$(ENV))

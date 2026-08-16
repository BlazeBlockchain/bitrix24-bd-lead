.PHONY: help version sync-versions bump-patch bump-minor bump-major release encrypt-skill dev up down build-web logs stop clean deploy-staging deploy-prod sync-tokens check-tokens build-icons check-icons

# Read the current version from VERSION file
VERSION := $(shell cat VERSION)

# Deployment configuration (overridable on the command line, e.g.
# `make deploy-staging DEPLOY_HOST=1.2.3.4`).
#
# DEPLOY_HOST matches vanguard-game and is a bare hostname, so it resolves only
# where an ssh config entry or /etc/hosts line defines it. If ssh reports
# "Could not resolve hostname", that is the missing piece — not a dead server.
DEPLOY_USER   ?= digaut
DEPLOY_HOST   ?= vmi1325117
DEPLOY_PATH   ?= ~/docker/bitrix24-bd-lead
STAGING_PATH  ?= ~/docker/bitrix24-bd-lead-staging

help:
	@echo "BD Lead Makefile"
	@echo ""
	@echo "Versioning:"
	@echo "  version           Print the current version ($(VERSION))"
	@echo "  sync-versions     Sync VERSION to all component files (package.json, manifest.json, config.py)"
	@echo "  bump-patch        Increment patch version, sync, and update CHANGELOG"
	@echo "  bump-minor        Increment minor version, sync, and update CHANGELOG"
	@echo "  bump-major        Increase major version, sync, and update CHANGELOG"
	@echo "  release           Commit and tag the release (assumes version already bumped + CHANGELOG edited)"
	@echo ""
	@echo "Design system:"
	@echo "  sync-tokens       Regenerate token blocks from design/tokens.css"
	@echo "  check-tokens      Fail if the token blocks drifted or legacy colors returned"
	@echo "  build-icons       Rasterize design/mark.svg to extension/icons/*.png"
	@echo "  check-icons       Validate the committed icons without regenerating"
	@echo ""
	@echo "Skill IP:"
	@echo "  encrypt-skill     Run the skill encryption script"
	@echo ""
	@echo "Docker Compose (dev):"
	@echo "  dev               Start full stack (db + backend + web) with --build"
	@echo "  up                Start full stack without rebuilding"
	@echo "  down              Stop all services"
	@echo "  build-web         Build web container only (fast iteration)"
	@echo "  logs              Follow logs for all services"
	@echo "  stop              Stop all services (alias for down)"
	@echo "  clean             Stop services and remove volumes"
	@echo ""
	@echo "Deploy:"
	@echo "  deploy-staging    SSH deploy with staging override"
	@echo "  deploy-prod       SSH deploy with production override"
	@echo ""
	@echo "  help              Show this help message"

version:
	@cat VERSION

sync-versions:
	@echo "Syncing version $(VERSION) to all components..."
	@python3 scripts/sync_versions.py
	@echo "Version sync complete!"

sync-tokens:
	@python3 scripts/sync_design_tokens.py

check-tokens:
	@python3 scripts/sync_design_tokens.py --check

build-icons:
	@python3 scripts/build_icons.py

check-icons:
	@python3 scripts/build_icons.py --check

bump-patch:
	@python3 scripts/bump_version.py patch
	@make sync-versions
	@python3 scripts/update_changelog.py

bump-minor:
	@python3 scripts/bump_version.py minor
	@make sync-versions
	@python3 scripts/update_changelog.py

bump-major:
	@python3 scripts/bump_version.py major
	@make sync-versions
	@python3 scripts/update_changelog.py

release:
	@echo "Preparing release for v$(VERSION)..."
	@make sync-versions
	@git add VERSION package.json web/package.json extension/manifest.json backend/app/config.py CHANGELOG.md
	@git commit -m "release: v$(VERSION)"
	@git tag -a v$(VERSION) -m "Release v$(VERSION)"
	@echo ""
	@echo "Release complete!"
	@echo "Next steps:"
	@echo "  git push --tags"
	@echo "  git push origin main"

encrypt-skill:
	@if [ -f scripts/encrypt_skill.py ]; then \
		python3 scripts/encrypt_skill.py; \
	else \
		echo "Error: scripts/encrypt_skill.py not found"; \
		echo "The skill encryption script has not been created yet."; \
		exit 1; \
	fi

# === Docker Compose (dev) ===

dev:
	docker compose -p bdlead-dev up --build -d --remove-orphans

up:
	docker compose -p bdlead-dev up -d

down:
	docker compose -p bdlead-dev down

build-web:
	docker compose -p bdlead-dev build --no-cache bdlead-web

logs:
	docker compose -p bdlead-dev logs -f

stop: down

clean:
	docker compose -p bdlead-dev down -v

# === Deploy ===
#
# These pull on the server rather than pushing the working tree. The previous
# rsync form shipped whatever happened to be on the operator's disk, including
# uncommitted edits, so the deployed artifact had no commit to point at and could
# not be reproduced. Pulling a named branch matches vanguard-game and means the
# running demo is always exactly some commit on origin.
#
# Prerequisites on the server, none of which these targets create:
#   - the repo cloned at $(DEPLOY_PATH) with read access to origin (GitHub)
#   - .env.staging / .env present there (gitignored, never transferred — see
#     .env.staging.example for what must be in it)
#   - the external `bbspace_net` docker network
#   - a location block in the shared nginx stack routing to the web container
# See docs/DEPLOY.md.

DEPLOY_BRANCH ?= ai-bd-assistant

deploy-staging:
	@echo "Deploying $(DEPLOY_BRANCH) to staging ($(DEPLOY_USER)@$(DEPLOY_HOST):$(STAGING_PATH))..."
	@ssh $(DEPLOY_USER)@$(DEPLOY_HOST) "\
	cd $(STAGING_PATH) && \
	git fetch origin && git checkout $(DEPLOY_BRANCH) && git pull origin $(DEPLOY_BRANCH) && \
	docker compose --env-file .env.staging \
	  -f docker-compose.yml -f docker-compose.staging.yml -p bdlead-staging \
	  up --build -d --remove-orphans"
	@echo "Staging deploy complete."

deploy-prod:
	@echo "Deploying $(DEPLOY_BRANCH) to production ($(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_PATH))..."
	@ssh $(DEPLOY_USER)@$(DEPLOY_HOST) "\
	cd $(DEPLOY_PATH) && \
	git fetch origin && git checkout $(DEPLOY_BRANCH) && git pull origin $(DEPLOY_BRANCH) && \
	docker compose --env-file .env \
	  -p bdlead-prod up --build -d --remove-orphans"
	@echo "Production deploy complete."

.DEFAULT_GOAL := help

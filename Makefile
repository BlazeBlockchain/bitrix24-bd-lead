.PHONY: help version sync-versions bump-patch bump-minor bump-major release encrypt-skill

# Read the current version from VERSION file
VERSION := $(shell cat VERSION)

help:
	@echo "SemVer Versioning Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  version           Print the current version ($(VERSION))"
	@echo "  sync-versions     Sync VERSION to all component files (package.json, manifest.json, config.py)"
	@echo "  bump-patch        Increment patch version, sync, and update CHANGELOG"
	@echo "  bump-minor        Increment minor version, sync, and update CHANGELOG"
	@echo "  bump-major        Increment major version, sync, and update CHANGELOG"
	@echo "  release           Commit and tag the release (assumes version already bumped + CHANGELOG edited)"
	@echo "  encrypt-skill     Run the skill encryption script"
	@echo "  help              Show this help message"

version:
	@cat VERSION

sync-versions:
	@echo "Syncing version $(VERSION) to all components..."
	@python3 scripts/sync_versions.py
	@echo "Version sync complete!"

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

.DEFAULT_GOAL := help

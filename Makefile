
.PHONY: clean
clean:
	rm -rf .python_packages
	rm -f logexport*.zip

.PHONY: lint
lint:
	mypy function_app.py logexport
	isort --check --diff --settings-file pyproject.toml logexport tests function_app.py
	black --check function_app.py logexport tests

.PHONY: fmt
fmt:
	isort --settings-file pyproject.toml logexport tests function_app.py
	black function_app.py logexport tests

protos: push.proto buf.gen.yaml buf.yaml
	buf generate .

# Package logexport in a zip file for Azure. The pattern should match the version.
logexport.%.zip:
	pip install --force-reinstall --target=".python_packages/lib/site-packages" $(@D)
	zip -r $@ host.json function_app.py .python_packages

.PHONY: release
release:
	@LATEST=$$(git fetch && git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0"); \
	MAJOR=$$(echo "$$LATEST" | cut -d. -f1); \
	MINOR=$$(echo "$$LATEST" | cut -d. -f2); \
	PATCH=$$(echo "$$LATEST" | cut -d. -f3); \
	case "$(BUMP)" in \
		major) MAJOR=$$((MAJOR + 1)); MINOR=0; PATCH=0 ;; \
		minor) MINOR=$$((MINOR + 1)); PATCH=0 ;; \
		patch) PATCH=$$((PATCH + 1)) ;; \
		*) echo "Invalid BUMP value: $(BUMP). Use major, minor, or patch." && exit 1 ;; \
	esac; \
	VERSION="$$MAJOR.$$MINOR.$$PATCH"; \
	echo "Tagging release $$VERSION" (was $$LATEST)"; \
	git tag -a "$$VERSION" -m "Release $$VERSION"; \
	echo "Tag $$VERSION created. Push with: git push origin $$VERSION"

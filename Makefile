
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


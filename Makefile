
.PHONY: clean
clean:
	rm -rf .python_packages
	rm -f logexport*.zip

.PHONY: lint
lint:
	mypy function_app.py logexport
	isort --skip "logexport/_version.py" -c function_app.py logexport/*
	black --check --exclude "logexport/_version.py" function_app.py logexport

protos: push.proto buf.gen.yaml buf.yaml
	buf generate .

# Package logexport in a zip file for Azure. The pattern should match the version.
logexport.%.zip:
	pip install --target=".python_packages/lib/site-packages" $(@D)
	zip -r $@ host.json function_app.py .python_packages



.PHONY: clean
clean:
	rm -rf .python_packages
	rm -f logexport.zip

.PHONY: protos
protos: push.proto buf.gen.yaml buf.yaml
	buf generate .

logexport.zip:
	pip install --target=".python_packages/lib/site-packages" $(@D) && \
	zip -r $@ host.json function_app.py .python_packages


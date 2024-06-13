An Azure function that consume eventhub messages and ships them to Grafana Loki / Grafana Cloud. 

It supports structured metadata, attribute based log filtering and default stream label pairs. 

Refer to [INSTALLATION.md](INSTALLATION.md) for the installation instructions
Refer to [DEVELOPER.md](DEVELOPER.md) how to run the unit tests and details about the working of the function.

# TODO 

- Retry mechanism on HTTP issues like rate limiting.
- Break up large POSTS into multiple POSTS to not run into message limits. 
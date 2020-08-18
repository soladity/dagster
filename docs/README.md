## Development

To work on the docs:

```
cd docs/next
yarn dev
```

If you make a change to the RST, make sure you run the following:

    make buildnext

## Deployment

### Before Deploying

- Make sure you have set the following env variables: `NEXT_ALGOLIA_APP_ID`, `NEXT_ALGOLIA_API_KEY`, `NEXT_ALGOLIA_ADMIN_KEY`.

### Instructions

To build and push docs for a new version (e.g. 0.8.5), in `docs` directory, run:

```
pip install -e python_modules/automation
dagster-docs build -v 0.8.5
```

.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

============
Introduction
============

Dagster is an opinionated system and programming model for data pipelines. This process goes by
many names -- ETL (extract-transform-load), ELT (extract-load-transform), model production, data
integration, and so on -- but in essence they all describe the same activity: Performing a set of
computations structured as a DAG (directed, acyclic graph) that end up producing data assets,
whether those assets be tables, files, machine-learning models, etc.

[![Coverage Status](https://coveralls.io/repos/github/dagster-io/dagster/badge.svg)](https://coveralls.io/github/dagster-io/dagster)

There are a few tools in this repo:

- **Dagster**: The core programming model and abstraction stack; a stateless single-node and -process execution engine; and a CLI tool for driving that engine.
* **Dagit**: Dagit is a rich viewer for Dagster assets.
* **Dagster GE**: A Dagster integration with Great Expectations. (see https://github.com/great-expectations/great_expectations)
* **Dagstermill**: An experimental prototype for integrating productionized notebooks into dagster pipelines. Built on the papermill library (https://github.com/nteract/papermill)

Go to https://dagster.readthedocs.io/en/latest/ for documentation!

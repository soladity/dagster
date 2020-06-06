---
title: Unit testing a pipeline
description: How to create a unit test for a pipeline
---

# Pipeline Unit Testing

This demonstrates how to execute a pipeline in a manner suitable
for unit testing. Here we focus on the mechanics and what APIs to use,
rather than how to design a pipeline such that resources are
abstracted away.

The workhouse function for unit-testing a pipeline is the `execute_pipeline`
function. Using this function one can execute a pipeline in process
and then test properties of the execution using the `PipelineExecutionResult`
object that it returns.

This function can also be used to execute a subset of a pipeline.

Finally we demonstrate how one can test against the event stream, which
is the most generic way that a solid communicates what happened during
its computation. Solids communicate events for starting, input and output
type checking, and for user-provided events such as expectations, materializations,
and outputs.

# Open in Playground

Open up this example in a playground using [Gitpod](https://gitpod.io)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#EXAMPLE=unittesting/https://github.com/dagster-io/dagster)

# Download Manually

Download the example:

```
curl https://codeload.github.com/dagster-io/dagster/tar.gz/master | tar -xz --strip=2 dagster-master/examples/unittesting
cd unittesting
```

from dagster_k8s.job import K8S_RESOURCE_REQUIREMENTS_KEY, get_k8s_resource_requirements

from dagster import solid


# CPU units are millicpu
# Memory units are MiB
def test_resource_tags():
    @solid(
        tags={
            K8S_RESOURCE_REQUIREMENTS_KEY: {
                'requests': {'cpu': '250m', 'memory': '64Mi'},
                'limits': {'cpu': '500m', 'memory': '2560Mi'},
            }
        }
    )
    def boop(_):
        pass

    resources = get_k8s_resource_requirements(boop.tags)
    assert resources.requests['cpu'] == '250m'
    assert resources.requests['memory'] == '64Mi'
    assert resources.limits['cpu'] == '500m'
    assert resources.limits['memory'] == '2560Mi'

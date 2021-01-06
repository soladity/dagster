class SupportedPython:
    V3_8 = "3.8.7"
    V3_7 = "3.7.9"
    V3_6 = "3.6.12"


SupportedPythons = [
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]


TOX_MAP = {
    SupportedPython.V3_8: "py38",
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
}


# https://github.com/dagster-io/dagster/issues/1662
DO_COVERAGE = True

# GCP tests need appropriate credentials
GCP_CREDS_LOCAL_FILE = "/tmp/gcp-key-elementl-dev.json"

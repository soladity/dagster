# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython(object):
    V3_7 = "3.7.4"
    V3_6 = "3.6.9"
    V3_5 = "3.5.7"
    V2_7 = "2.7.16"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

SupportedPython3s = [SupportedPython.V3_7, SupportedPython.V3_6, SupportedPython.V3_5]

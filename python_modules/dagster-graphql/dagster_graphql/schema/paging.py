from dagster_graphql import dauphin


class DauphinCursor(dauphin.Int, dauphin.Scalar):
    class Meta(object):
        name = "Cursor"

from dagster import Float, In, InputDefinition, Int, List, Out, OutputDefinition, graph, op


@op(out=Out(Int))
def emit_one():
    return 1


@op(ins={"numbers": In(List[Int])}, out=Out(Int))
def add(numbers):
    return sum(numbers)


@op(ins={"num": In(Float)}, out=Out(Float))
def div_two(num):
    return num / 2


@graph(output_defs=[OutputDefinition(Int)])
def emit_two():
    return add([emit_one(), emit_one()])


@graph(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
def add_four(num):
    return add([emit_two(), emit_two(), num])


@graph(input_defs=[InputDefinition("num", Float)], output_defs=[OutputDefinition(Float)])
def div_four(num):
    return div_two(num=div_two(num))


@op(ins={"num": In(Int)}, out=Out(Float))
def int_to_float(num):
    return float(num)


@graph
def composition():
    div_four(int_to_float(add_four()))


composition_job = composition.to_job(description="Demo job that makes use of composite ops.")

from testproto.grpc.dummy_pb2_grpc import DummyServiceServicer


class IncompleteServicer(DummyServiceServicer):
    pass


incomplete = IncompleteServicer()

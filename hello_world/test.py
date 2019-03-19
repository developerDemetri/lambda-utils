from . import index

def test_hello_world_handler():
    assert index.hello_world_handler(None, None) is None

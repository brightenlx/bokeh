from __future__ import absolute_import

import pytest

from bokeh.protocol import receiver, Protocol
from bokeh.protocol.exceptions import ValidationError

_proto = Protocol("1.0")

def test_creation():
    receiver.Receiver(None)

def test_validation_success():
    msg = _proto.create('ACK')
    r = receiver.Receiver(_proto)

    partial = r.consume(msg.header_json).result()
    assert partial is None

    partial = r.consume(msg.metadata_json).result()
    assert partial is None

    partial = r.consume(msg.content_json).result()
    assert partial is not None
    assert partial.msgtype == msg.msgtype
    assert partial.header == msg.header
    assert partial.content == msg.content
    assert partial.metadata == msg.metadata

def test_validation_success_with_one_buffer():
    r = receiver.Receiver(_proto)

    partial = r.consume(b'{"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers":1}').result()
    assert partial is None

    partial = r.consume(b'{}').result()
    assert partial is None

    partial = r.consume(b'{"bar": 10}').result()
    assert partial is None

    partial = r.consume(b'header').result()
    assert partial is None

    partial = r.consume(b'payload').result()
    assert partial is not None
    assert partial.msgtype == "PATCH-DOC"
    assert partial.header == {"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers":1}
    assert partial.content == {"bar":10}
    assert partial.metadata == {}
    assert partial.buffers == [('header', b'payload')]

def test_multiple_validation_success_with_multiple_buffers():
    r = receiver.Receiver(_proto)

    for N in range(10):
        partial = r.consume(b'{"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers":%d}' % N).result()
        partial = r.consume(b'{}').result()
        partial = r.consume(b'{"bar": 10}').result()

        for i in range(N):
            partial = r.consume(b'header%d' % i).result()
            partial = r.consume(b'payload%d' % i).result()

        assert partial is not None
        assert partial.msgtype == "PATCH-DOC"
        assert partial.header == {"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers": N}
        assert partial.content == {"bar":10}
        assert partial.metadata == {}
        assert partial.buffers == [('header%d' % i, b'payload%d' %i) for i in range(N)]

def test_binary_header_raises_error():
    r = receiver.Receiver(_proto)

    with pytest.raises(ValidationError):
        r.consume(b'header').result()

def test_binary_metadata_raises_error():
    r = receiver.Receiver(_proto)

    r.consume(b'header')
    with pytest.raises(ValidationError):
        r.consume(b'metadata').result()

def test_binary_content_raises_error():
    r = receiver.Receiver(_proto)

    r.consume(b'header')
    r.consume(b'metadata')
    with pytest.raises(ValidationError):
        r.consume(b'content').result()

def test_binary_payload_header_raises_error():
    r = receiver.Receiver(_proto)

    r.consume(b'{"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers":1}')
    r.consume(b'{}')
    r.consume(b'{}')
    with pytest.raises(ValidationError):
        r.consume(b'buf_header').result()

def test_text_payload_buffer_raises_error():
    r = receiver.Receiver(_proto)

    r.consume(b'{"msgtype": "PATCH-DOC", "msgid": "10", "num_buffers":1}')
    r.consume(b'{}')
    r.consume(b'{}')
    r.consume(b'buf_header').result()
    with pytest.raises(ValidationError):
        r.consume(b'buf_payload').result()

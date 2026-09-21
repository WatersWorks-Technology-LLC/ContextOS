import pytest
from contextos.codecs.ncc_vcl import NCCVCLCodec
from contextos.codecs.structured_text import StructuredTextCodec
from contextos.codecs.vcl_svg import VCLSVGRenderer

def test_unit_ncc_vcl():
    assertions = [{"kind": "fact", "status": "current", "subject": "DB", "predicate": "depends_on", "object": "Postgres", "source_ref": "S1"}]
    encoded, checksum = NCCVCLCodec.encode_packet(assertions, ["Rule 1"])
    assert "[MUST] Rule 1" in encoded
    assert "[CURR:FACT] DB -> Postgres" in encoded
    assert len(checksum) == 8

def test_unit_vcl_svg():
    nodes = [{"id": "auth.py", "label": "Auth Module"}]
    edges = []
    svg = VCLSVGRenderer.render_graph_svg(nodes, edges)
    assert "<svg" in svg
    assert "Auth Module" in svg

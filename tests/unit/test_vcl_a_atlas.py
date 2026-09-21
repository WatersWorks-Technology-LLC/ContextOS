import pytest
from contextos.codecs.vcl_a_atlas import VCLAAtlasRenderer

def test_vcl_a_token_profiler():
    # Test per-model vision token profiling
    t_gpt = VCLAAtlasRenderer.calculate_vision_tokens(4096, "gpt-4o")
    assert t_gpt["model_name"] == "gpt-4o"
    assert t_gpt["estimated_visual_cost"] > 1000
    assert t_gpt["actual_billed_input_units"] > 1000

    t_gemini = VCLAAtlasRenderer.calculate_vision_tokens(2048, "gemini-1.5-pro")
    assert t_gemini["actual_billed_input_units"] == 258

    t_qwen = VCLAAtlasRenderer.calculate_vision_tokens(1024, "qwen2-vl-7b")
    assert t_qwen["actual_billed_input_units"] > 0

def test_vcl_a_multi_resolution_rendering():
    assertions = [{"id": "A1", "kind": "state", "subject": "DB", "predicate": "engine", "object": "sqlite"}]
    invariants = ["NO_GLOBAL_MUTATION"]

    for res in [1024, 2048, 4096]:
        svg_text, checksum = VCLAAtlasRenderer.render_atlas_svg(
            assertions=assertions,
            invariants=invariants,
            resolution=res
        )
        assert f'width="{res}"' in svg_text
        assert len(checksum) == 8

def test_vcl_a_multimodal_benchmark():
    res = VCLAAtlasRenderer.run_multimodal_qa_benchmark("gpt-4o", 2048)
    assert res["model_name"] == "gpt-4o"
    assert res["disaggregated_metrics"]["node_recognition_accuracy"] >= 0.90
    assert res["ready_for_production"] is False

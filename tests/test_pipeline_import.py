"""Test that pipeline imports and MODEL instantiates correctly."""


def test_litellm_model_instantiation():
    from google.adk.models.lite_llm import LiteLlm

    model = LiteLlm(model="openrouter/qwen/qwen3.5-plus-20260420")
    assert model is not None


def test_pipeline_import():
    import pipeline  # noqa: F401

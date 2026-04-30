def test_studio_app_imports_without_error():
    import importlib
    mod = importlib.import_module("studio.app")
    assert hasattr(mod, "main")


def test_studio_components_helpers_importable():
    from studio.components import compile_and_run, lex_only, parse_only
    assert callable(compile_and_run)
    assert callable(lex_only)
    assert callable(parse_only)

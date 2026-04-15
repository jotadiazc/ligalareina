from web_app import FixtureWebHandler


def test_render_page_contains_title() -> None:
    html = FixtureWebHandler._render_page(FixtureWebHandler)  # type: ignore[arg-type]
    assert "Administrador de liga (versión web)" in html
    assert "Generar fixture" in html

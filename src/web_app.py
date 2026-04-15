from __future__ import annotations

import html
import json
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from league_scheduler import build_output, generate_schedule

DEFAULT_JSON = {
    "name": "Liga Municipal",
    "series": [
        {
            "name": "Serie A",
            "teams": [
                {"name": "Mapuches", "rules": {"no_play_weekdays": [6]}},
                {"name": "Halcones"},
                {"name": "Tigres"},
                {"name": "Cóndores"},
            ],
        }
    ],
}


class FixtureWebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self._respond_html(self._render_page())

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(raw_body)

        payload_str = data.get("payload", [json.dumps(DEFAULT_JSON, ensure_ascii=False, indent=2)])[0]
        start_date = data.get("start_date", [date.today().isoformat()])[0]
        round_interval_days = int(data.get("round_interval_days", ["7"])[0])
        max_shift_days = int(data.get("max_shift_days", ["3"])[0])

        result = ""
        error = ""

        try:
            payload = json.loads(payload_str)
            schedule = generate_schedule(
                payload,
                start_date=date.fromisoformat(start_date),
                round_interval_days=round_interval_days,
                max_shift_days=max_shift_days,
            )
            result = json.dumps(build_output(schedule), ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - UI error path
            error = str(exc)

        self._respond_html(
            self._render_page(
                payload_str=payload_str,
                start_date=start_date,
                round_interval_days=round_interval_days,
                max_shift_days=max_shift_days,
                result=result,
                error=error,
            )
        )

    def _respond_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _render_page(
        self,
        payload_str: str | None = None,
        start_date: str | None = None,
        round_interval_days: int = 7,
        max_shift_days: int = 3,
        result: str = "",
        error: str = "",
    ) -> str:
        payload = payload_str or json.dumps(DEFAULT_JSON, ensure_ascii=False, indent=2)
        start = start_date or date.today().isoformat()

        return f"""<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Generador de Fixtures</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 2rem; }}
      textarea {{ width: 100%; min-height: 260px; font-family: monospace; }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
      .error {{ color: #b42318; font-weight: bold; }}
      pre {{ background: #f5f5f5; padding: 1rem; overflow-x: auto; }}
      label {{ display: block; margin-top: .6rem; }}
      button {{ margin-top: 1rem; padding: .6rem 1rem; }}
    </style>
  </head>
  <body>
    <h1>Administrador de liga (versión web)</h1>
    <p>Pega el JSON de la liga y genera el fixture automático con restricciones por equipo.</p>
    <form method=\"post\">
      <div class=\"grid\">
        <div>
          <label for=\"payload\">Liga (JSON)</label>
          <textarea id=\"payload\" name=\"payload\">{html.escape(payload)}</textarea>
        </div>
        <div>
          <label for=\"start_date\">Fecha inicial (YYYY-MM-DD)</label>
          <input id=\"start_date\" name=\"start_date\" value=\"{html.escape(start)}\" />

          <label for=\"round_interval_days\">Días entre rondas</label>
          <input id=\"round_interval_days\" name=\"round_interval_days\" type=\"number\" value=\"{round_interval_days}\" />

          <label for=\"max_shift_days\">Máximo corrimiento (±días)</label>
          <input id=\"max_shift_days\" name=\"max_shift_days\" type=\"number\" value=\"{max_shift_days}\" />

          <button type=\"submit\">Generar fixture</button>
        </div>
      </div>
    </form>
    {f'<p class="error">Error: {html.escape(error)}</p>' if error else ''}
    {f'<h2>Resultado</h2><pre>{html.escape(result)}</pre>' if result else ''}
  </body>
</html>"""


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), FixtureWebHandler)
    print(f"Servidor web disponible en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

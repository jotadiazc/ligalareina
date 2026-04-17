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
        table_html = self._render_result_table(result) if result else ""
        summary_html = self._render_summary(result) if result else ""

        return f"""<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Panel Liga Reina</title>
    <style>
      :root {{
        --bg: #0f172a;
        --card: #111827;
        --border: #24324d;
        --muted: #94a3b8;
        --text: #e2e8f0;
        --accent: #22c55e;
        --danger: #fda4af;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, Arial, sans-serif;
        background: linear-gradient(180deg, #0f172a, #111827 30%);
        color: var(--text);
      }}
      main {{ max-width: 1200px; margin: 0 auto; padding: 1.5rem; }}
      .hero {{
        border: 1px solid var(--border);
        background: rgba(15, 23, 42, 0.8);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
      }}
      .hero p {{ margin: .4rem 0 0; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: 1.2fr .8fr; gap: 1rem; }}
      .panel {{
        border: 1px solid var(--border);
        background: var(--card);
        border-radius: 16px;
        padding: 1rem;
      }}
      textarea {{
        width: 100%;
        min-height: 420px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        border-radius: 8px;
        border: 1px solid var(--border);
        background: #0b1220;
        color: var(--text);
        padding: .75rem;
      }}
      input {{
        width: 100%;
        border-radius: 8px;
        border: 1px solid var(--border);
        background: #0b1220;
        color: var(--text);
        padding: .55rem .65rem;
      }}
      label {{ display: block; margin-top: .85rem; color: var(--muted); }}
      button {{
        margin-top: 1rem;
        width: 100%;
        border: 0;
        border-radius: 10px;
        background: linear-gradient(90deg, #22c55e, #16a34a);
        color: white;
        font-weight: 700;
        padding: .72rem;
        cursor: pointer;
      }}
      .error {{
        color: var(--danger);
        background: rgba(190, 24, 93, .1);
        border: 1px solid rgba(190, 24, 93, .35);
        padding: .75rem;
        border-radius: 8px;
      }}
      .stats {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: .75rem;
        margin-bottom: .8rem;
      }}
      .stat {{
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: .65rem;
        background: #0b1220;
      }}
      .stat b {{ display: block; font-size: 1.1rem; }}
      table {{
        width: 100%;
        border-collapse: collapse;
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
      }}
      th, td {{
        border-bottom: 1px solid var(--border);
        padding: .6rem;
        text-align: left;
        font-size: .9rem;
      }}
      th {{ background: #0b1220; color: #cbd5e1; }}
      pre {{
        margin-top: .8rem;
        background: #0b1220;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: .8rem;
        overflow-x: auto;
      }}
      @media (max-width: 900px) {{
        .grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class=\"hero\">
        <h1>Administrador de liga (versión web)</h1>
        <p>Panel para visualizar y administrar campeonatos: equipos, rondas y fixture automático con reglas por equipo.</p>
      </section>
      <form method=\"post\">
        <div class=\"grid\">
          <section class=\"panel\">
            <label for=\"payload\">Liga (JSON)</label>
            <textarea id=\"payload\" name=\"payload\">{html.escape(payload)}</textarea>
          </section>
          <section class=\"panel\">
            <h2>Configuración</h2>
            <label for=\"start_date\">Fecha inicial (YYYY-MM-DD)</label>
            <input id=\"start_date\" name=\"start_date\" value=\"{html.escape(start)}\" />

            <label for=\"round_interval_days\">Días entre rondas</label>
            <input id=\"round_interval_days\" name=\"round_interval_days\" type=\"number\" value=\"{round_interval_days}\" />

            <label for=\"max_shift_days\">Máximo corrimiento (±días)</label>
            <input id=\"max_shift_days\" name=\"max_shift_days\" type=\"number\" value=\"{max_shift_days}\" />

            <button type=\"submit\">Generar fixture</button>
          </section>
        </div>
      </form>
      {f'<p class="error">Error: {html.escape(error)}</p>' if error else ''}
      {f'<section class="panel"><h2>Resumen</h2>{summary_html}</section>' if result else ''}
      {f'<section class="panel"><h2>Partidos programados</h2>{table_html}<h3>JSON generado</h3><pre>{html.escape(result)}</pre></section>' if result else ''}
    </main>
  </body>
</html>"""

    @staticmethod
    def _render_result_table(result: str) -> str:
        try:
            rows = json.loads(result)
        except json.JSONDecodeError:
            return "<p>No se pudo procesar el resultado.</p>"

        if not rows:
            return "<p>No hay partidos generados.</p>"

        body = "".join(
            (
                "<tr>"
                f"<td>{html.escape(str(r.get('serie', '')))}</td>"
                f"<td>{html.escape(str(r.get('round', '')))}</td>"
                f"<td>{html.escape(str(r.get('match', '')))}</td>"
                f"<td>{html.escape(str(r.get('home', '')))}</td>"
                f"<td>{html.escape(str(r.get('away', '')))}</td>"
                f"<td>{html.escape(str(r.get('date', '')))}</td>"
                f"<td>{'Sí' if r.get('forced_restriction') else 'No'}</td>"
                "</tr>"
            )
            for r in rows
        )

        return (
            "<table><thead><tr>"
            "<th>Serie</th><th>Ronda</th><th>Partido</th><th>Local</th><th>Visita</th><th>Fecha</th><th>Forzado</th>"
            f"</tr></thead><tbody>{body}</tbody></table>"
        )

    @staticmethod
    def _render_summary(result: str) -> str:
        try:
            rows = json.loads(result)
        except json.JSONDecodeError:
            return "<p>No disponible.</p>"

        total_matches = len(rows)
        forced_matches = sum(1 for row in rows if row.get("forced_restriction"))
        series = {str(row.get("serie", "")) for row in rows}
        unique_dates = {str(row.get("date", "")) for row in rows}

        return (
            "<div class='stats'>"
            f"<article class='stat'><span>Total partidos</span><b>{total_matches}</b></article>"
            f"<article class='stat'><span>Partidos forzados</span><b>{forced_matches}</b></article>"
            f"<article class='stat'><span>Series activas</span><b>{len(series)}</b></article>"
            f"<article class='stat'><span>Fechas con juego</span><b>{len(unique_dates)}</b></article>"
            "</div>"
        )


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), FixtureWebHandler)
    print(f"Servidor web disponible en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

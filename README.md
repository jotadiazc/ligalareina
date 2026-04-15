# Administrador de liga de fútbol (fixtures con reglas)

Aplicación en Python para administrar una liga por series y generar fixtures automáticos.

## Versiones disponibles

- **CLI** (línea de comandos)
- **Web local** (interfaz en navegador)

## Qué soporta

- Múltiples series dentro de una misma liga.
- Múltiples equipos por serie.
- Generación automática round-robin por serie.
- Reglas por equipo para días en los que **evita** jugar (`no_play_weekdays`).
- Si no hay alternativa dentro del rango permitido, se agenda igual y se marca como `forced_restriction=true` (caso "estrictamente necesario").

## Formato de entrada

Archivo JSON con estructura:

```json
{
  "name": "Liga Municipal",
  "series": [
    {
      "name": "Serie A",
      "teams": [
        {
          "name": "Mapuches",
          "rules": {
            "no_play_weekdays": [6]
          }
        }
      ]
    }
  ]
}
```

Días de semana:

- `0` lunes
- `1` martes
- `2` miércoles
- `3` jueves
- `4` viernes
- `5` sábado
- `6` domingo

## Uso CLI

```bash
python src/main.py \
  --input example_league.json \
  --start-date 2026-04-19 \
  --round-interval-days 7 \
  --max-shift-days 3 \
  --output fixture_output.json
```

## Uso versión web

```bash
python src/web_app.py
```

Luego abre en tu navegador: `http://127.0.0.1:8000`

En la web puedes:

- pegar/editar el JSON de la liga,
- definir fecha inicial,
- definir intervalo de rondas,
- definir corrimiento máximo,
- generar y ver el fixture en pantalla.

## Salida

JSON con la lista de partidos:

- `serie`
- `round`
- `match`
- `home`
- `away`
- `date`
- `forced_restriction`
- `notes`


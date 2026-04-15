# Administrador de liga de fútbol (fixtures con reglas)

Aplicación CLI en Python para administrar una liga por series y generar fixtures automáticos.

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

## Uso

```bash
python src/main.py \
  --input example_league.json \
  --start-date 2026-04-19 \
  --round-interval-days 7 \
  --max-shift-days 3 \
  --output fixture_output.json
```

> Si `Mapuches` no juega domingo (`6`), el generador intentará mover ese partido ±3 días. Si no puede, lo deja en domingo y agrega una nota de restricción forzada.

## Salida

Un JSON con la lista de partidos:

- `serie`
- `round`
- `match`
- `home`
- `away`
- `date`
- `forced_restriction`
- `notes`


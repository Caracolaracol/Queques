# AGENTS.md — Bagels (fork "caracol")

Tracker de gastos en TUI. **Fork local de [EnhancedJax/Bagels](https://github.com/EnhancedJax/Bagels)**
(el repo upstream está inactivo: último release v0.3.12, jul 2025). Rama de trabajo: `caracol`.

## Stack

- Python 3.13+ · TUI con **Textual** · **SQLAlchemy + SQLite** · config con **pydantic** · paquetes con **uv**
- El paquete instalado es una **copia** de este repo: tras editar código hay que
  re-sincronizar → `cd ~/code/bagels && uv tool install --from . bagels`
- Revertir al upstream: `uv tool install bagels`

## Comandos

```bash
uv run bagels                 # correr en modo dev (desde ~/code/bagels)
bagels                        # versión instalada (nuestro fork)
bagels locate config|database # rutas de config/datos
bagels --at /tmp/mi_dir       # usar otro directorio (pruebas SIN tocar datos reales)
uv tool install --from . bagels   # re-sincronizar la instalación tras editar
uv tool install bagels            # volver al original
uv run pytest                 # tests (ver "Gotchas": algunos fallan pre-existentes)
```

Rutas de datos reales: config `~/.config/bagels/config.yaml` · BD `~/.local/share/bagels/db.db`.

## Estructura (`src/bagels/`)

| Ruta | Contenido |
|---|---|
| `bagel.py`, `__main__.py` | entrypoint CLI (click) |
| `app.py` | app Textual principal |
| `home.py` | pantalla principal; monta los módulos |
| `components/modules/` | módulos de UI: `budgets.py`, `categories.py`, `records/`, `insights.py`, `accountmode.py`, `datemode.py`, `spending/`, `templates.py`, `welcome.py` |
| `components/datatable.py` | tabla custom — **el formato de floats se define acá** |
| `models/` | SQLAlchemy: `account`, `category`, `person`, `record`, `record_template`, `split`; `database/app.py` (init_db, sync) |
| `managers/` | lógica de negocio: `accounts`, `categories`, `persons`, `records`, `record_templates`, `utils`, `splits` |
| `forms/`, `modals/` | formularios y modales |
| `config.py` | `CONFIG` (pydantic), `load_config()`, `write_state()` |
| `locations.py` | paths (`set_custom_root`, `config_file`, `database_file`) |
| `themes.py` | `Theme` + `BUILTIN_THEMES` (temas hardcodeados, no custom por config) |
| `styles/*.tcss` | CSS de Textual |
| `utils/format.py` | `parse_formula_expression`, `money_str`, formateo de fechas |
| `provider.py` | command palette (Ctrl+P): temas, toggle footer, abrir config... |

## Nuestras features (fork)

1. **Presupuesto mensual por categoría** (módulo Budgeting → sección "Category budgets"):
   - Columna `monthlyBudget` en `models/category.py`
   - `managers/categories.py`: `get_category_budget_rows(offset)` (gasto del mes por categoría
     padre, rollup de subcategorías, excluye income y transfers) y `update_category_budget(id, amount)`
   - UI en `components/modules/budgets.py`: input por fila, **se guarda con Enter**
     (`on_input_submitted`), labels spent/left en verde/rojo
2. **Montos sin decimales** (CLP): `round_decimals = 0`; la datatable formatea floats con
   `CONFIG.defaults.round_decimals`; `utils/format.py::money_str()` para labels;
   los restricts de inputs de montos se vuelven `\d*` (enteros) cuando round_decimals == 0.
3. **Módulo People removido de la UI** (usuario único): fuera de `manager.py` (import,
   instanciación, rebuild, yield) y de la entrada del jumper en `app.py` (`people-container`).
   El modelo/manager de personas y los splits de registros quedan intactos.
4. **Modo "Display by Person" removido de Records**: sin botón `Person (w)`, sin hotkey
   `display_by_person` (también fuera de config.py y del config.yaml), sin la vista por
   persona en `_table_builder.py` (DisplayMode solo tiene DATE) y sin el case "p" de
   edición en `records/_cud.py`. Los splits por persona en el formulario de registro
   siguen funcionando (solo aparecen al togglear splits con `s`).
5. **Wishlist reordenable** (módulo Wishlist): columna `position` en `models/wishlist.py`
   (nullable, auto-migrada; backfill self-healing en `managers/wishlist.py::_backfill_positions`
   — filas viejas reciben su `id`). `get_wishlist_items` ordena por `(position, id)`;
   `add_wishlist_item` usa `max(position)+1`; `move_wishlist_item(id, ±1)` intercambia
   posiciones con el vecino (no-op en bordes o id desconocido). UI: `Shift+↑/↓` (y
   `Ctrl+↑/↓` ocultos) en `components/modules/wishlist.py`; el rebuild reselecciona por id
   para que el cursor siga al item movido. Tests: `tests/managers/test_wishlist.py`
   (8 tests, patrón in-memory + swap de Session).
6. **Records: tabla ajustada + barra de detalles** (`components/modules/records/`):
   `_table_builder.py` construye las filas en dos pasas (contenido y luego anchos) y
   trunca con `…` — caps adaptativos `self._cat_cap`/`self._acc_cap` según el ancho del
   módulo, columna Label elástica (mínimo 8). Montos con `money_str` (sin `.0`).
   Barra `#record-details` bajo la tabla con label completo + meta (fecha · categoría ·
   cuenta · monto · splits) de la fila seleccionada, vía `self._row_details[key]`,
   actualizada en `on_data_table_row_highlighted` y al final de `rebuild` (cursor inicial
   en la primera fila con detalles, `_first_detail_row`). `on_resize` → `rebuild` para
   re-medir columnas. Backstop: `default_cell_formatter` en `datatable.py` aplica
   `overflow="ellipsis"` a celdas no-wrap. Gotcha: `rich.Text.truncate` es **in-place**
   y devuelve `None`.

## Gotchas (importantes)

- **Schema auto-migra**: `_sync_database_schema()` (models/database/app.py) hace
  `ALTER TABLE ADD COLUMN` al arrancar. Agregar una columna al modelo basta — NO hay
  migraciones manuales.
- **CONFIG**: en scripts hay que llamar `load_config()` antes de usar `CONFIG`
  (los tests del repo no lo hacen → por eso 20 tests fallan pre-existentes con
  `AttributeError: 'NoneType' object has no attribute 'defaults'` — **no son de nuestro fork**).
- Los tests además necesitan `freezegun` (no está en `dev-dependencies`): `uv pip install freezegun`.
- **Probar sin tocar la BD real**: `from bagels.locations import set_custom_root; set_custom_root("/tmp/x")`
  ANTES de importar `bagels.models.database.app`.
- `dynamic_cache` (managers/utils.py) crea un `lru_cache()` nuevo por llamada → no cachea entre llamadas.
- **Textual**: rebuild en cada keystroke pierde el foco del Input → persistir con Enter
  (`on_input_submitted`), no con `on_input_changed`.
- **Wishlist**: `rebuild()` reselecciona por **id del item** (no por índice) para que el
  cursor siga al item al reordenar. El binding `Enter` togglea done vía evento
  `ListView.Selected`; no usar `ctrl+j` como atajo (en terminal = Enter).
- Categorías default al primer arranque: 11 padres + 4 subcategorías c/u (ids 1–55).
- El repo se clonó con `--depth 1` (historial shallow).
- Temas `caracol` y `papel` disponibles en `themes.py` (`BUILTIN_THEMES`). `caracol` usa la paleta cerise/violet/ocre/platinum; `papel` usa la paleta clara compartida con fondo cálido `#FFF5C8`. El tema activo se elige en `state.theme` de `~/.config/bagels/config.yaml` (actualmente `papel`).

## Convenciones

- Commits en español, estilo convencional (`feat:`, `fix:`).
- Los tests corren con `uv run pytest` (espera fallos pre-existentes listados arriba).

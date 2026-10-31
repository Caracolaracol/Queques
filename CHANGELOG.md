# Changelog

## Unreleased (fork caracol)

- Records: removidos los **filtros** (inputs de categoría/monto/label y toggle) y el
  botón **Date (q)** — este último no hacía nada (solo existía el modo DATE). La tabla
  ocupa ahora toda la altura del módulo. La hotkey `display_by_date` también salió de
  `config.py` y del `config.yaml`.
- Records: nueva **columna Date** (`dd/mm`, según `defaults.date_format`) por fila —
  se eliminaron los group headers con rangos de semana (`25/10 - 01/11`); cada registro
  muestra su fecha directamente y los splits muestran su fecha de pago.
- Records: la tabla **se ajusta al ancho del módulo** — sin scroll horizontal ni
  texto cortado a mitad de palabra. Columnas Category/Account con tope adaptativo
  al ancho, Label elástico y truncado con `…` en todas las celdas. Nueva **barra
  de detalles** bajo la tabla con el contenido completo (label, fecha, categoría,
  cuenta, monto, splits) de la fila seleccionada: sigue el cursor del teclado, sin
  depender del mouse. Además los montos de la tabla ahora usan `money_str`
  (sin `.0` en CLP; antes se filtraban como float crudo).
- Nuevo módulo **Service accounts** en Home (reemplaza a Templates en esa
  columna): guarda números de cuenta de clientes por proveedor externo
  (proveedor + número + alias + notas), con edición y archivado (soft-delete
  vía `deletedAt`). Dedupe case-insensitive por proveedor+número. Tabla
  `service_account` auto-creada por schema sync. El módulo Templates ya no se
  monta en Home; las plantillas siguen disponibles desde el modal de records
  (`ctrl+t`).
- Wishlist: **reordenar por prioridad** — `Shift+↑`/`Shift+↓` (o `Ctrl+↑`/`Ctrl+↓`)
  mueven el item seleccionado un puesto arriba/abajo; el cursor sigue al item
  movido para repeticiones rápidas. Nueva columna `position` (auto-migrada por
  schema sync; filas existentes reciben su `id` como orden inicial = mismo orden
  de creación de siempre). Orden persistente en la BD.
- Budgeting: las categorías **padre con subcategorías ya no tienen input** — su
  budget se muestra read-only como la **suma automática de los budgets de sus
  subcategorías** (left = suma - gastado). Solo las categorías hoja y subcategorías
  son editables. El Total suma por nivel 0 sin doble conteo.
- Wishlist: fix de borrado/toggle — el ListView no resaltaba ningún item al montar
  (index None), así que `d` y `Espacio` no tenían objetivo. Ahora el primer item
  queda auto-seleccionado y la selección se preserva tras cada rebuild.
- Nuevo módulo **Wishlist** (lista de deseos) en el Manager, debajo de Categories:
  input para agregar items, `Enter`/`Espacio` para marcar hecho (✓/○), `d` para
  borrar. Persistente en la BD (tabla `wishlist`, auto-creada por schema sync).
- Budgeting: fila **Total** arreglada — el `border-top` consumía la única fila de la
  fila anclada, dejando el contenido invisible. Ahora mide 2 filas (borde + contenido)
  y se verifica por render real (SVG) que "Total | budget | spent | left" aparece
  siempre en la última fila del módulo.
- Budgeting: el módulo **Spending** queda oculto en el Manager para que la tabla de
  budgets use todo el espacio (con scroll vertical si hace falta). Se puede
  re-habilitar quitando el `display: none` en manager_modules.tcss.
- Budgeting: fila **Total** al final de la tabla (negrita, borde superior): budget =
  suma de todos los budgets definidos (incluye subcategorías), spent = gasto real del
  mes (suma de categorías padre, sin doble conteo), left = diferencia en verde/rojo.
- Budgeting: la tabla de budgets de categoría ahora muestra **subcategorías** indentadas bajo
  su padre (spent del padre = rollup de hijos) y tiene **formato de tabla** con header
  (Category/Budget/Spent/Left) y filas con estilo **zebra**. Al guardar con Enter se
  muestra una notificación de confirmación.
- Budgeting: las categorías usadas solo para ingreso (ej. Salary) ya no aparecen en la
  lista de budgets de categoría (se filtra por uso de records: income-only se excluye).
- Sin decimales en montos: inputs de budget (mensual, savings, wants), balances de cuentas,
  insights (neto/promedio), modal de transferencias y plantillas usan `money_str`
  (respeta `round_decimals=0` para CLP).
- Temas "caracol" (oscura; paleta personal: cerise, violet, lavanda, ocre, platinum) y
  "papel" (clara, fondo cálido `#FFF5C8`) agregados a `BUILTIN_THEMES`. El tema activo
  se elige en `state.theme` del config (actualmente `papel`).
- Records de la vista principal pasan de semanales a mensuales (`defaults.period: month` en config).

## 0.3.12

- Sort people in manager page by net due
- Fixed: Crash when selecting parent category in record modal

## 0.3.11

- Shows parent category name in record modal
- Updated config documentation on income
- Fixed: Record modal not using dynamic mode values
- Fixed: Autocomplete validation for options with same text

## 0.3.10

- Configurable hotkey for submit and template
- Changed default record modal hotkeys
- Expose additional fields in record creation modal
- Amount rounding validation
- Changed default theme to tokyo-night

## 0.3.9

- Relaxed dependency restrictions

## 0.3.8

- Fixed: Balance not updating when adding records

## 0.3.7

- New! New transfer modal now has autocomplete.
- Include item name in delete confirmation messages
- Fixed: Templates with similar names will now be selected correctly
- Fixed: Crash when adding new account

## 0.3.6

- Added ActualBudget migration
- Fixed datemode styling

## 0.3.4

- Added ability to click on accounts in accounts-mode module
- Fix: Focus removed when switching to persons with empty view

## 0.3.2

- Added error message and user prompt when config error

## 0.3.0

- New! Label, amount and category filters in records module!
- New! Manager page to view your categories and people.
- New! Spending plottings / graphs with estimated spendings!
- New! Budgetting tool for saving money and limiting unnecessary spendings
- Fixed bugs
- Removed barchart in insights.

## 0.2.7

- Fix record module input and loading issues.

## 0.2.6

- Bumped textual to 1.0.0
- Fixed: Account field not required when creating paid split
- Fixed: Beginning balance 0 will pass validation but does not pass non-null constraint

## 0.2.5

- Fixed: Typo in update command

## 0.2.4

- Fixed: Crash when changing offset without app being ready

## 0.2.3

- Added amounts in insight bar legends
- Autocomplete to use templates in label field
- Shift enter to create templates along with a non-transfer record
- Auto update checks
- Fixed: Inconsistent tab behaviors

## 0.2.2

- Fix: remove obscure dependencies

## 0.2.1

- Lock dependencies, rookie mistake

## 0.2.0

- Added formula inputs in amount fields!

## 0.1.16

- Updated bar visuals for non-rounded variation
- WIP Budgets
- WIP Tests

## 0.1.15

- Fix: Deleted categories visible

## 0.1.14

- Fix: Lock textual version and defer upgrade to future

## 0.1.13

- Fix: Income record split value should be subtracted, not added, to the account balance

## 0.1.12

- Added total amount in persons view
- Fix: Transfers not using active date

## 0.1.11

- Add transfers as templates.
- Fix: Crash when go to date in calendar
- Fix: Not creating and using custom config file

## 0.1.10

- View by accounts is now an app action. Records will be filtered as well in that view.
- Fix: Not using active filter date when creating a paid split
- Fix: Crash when entering scientific notation / negative numbers in the amount field
- Fix: New record modal having extra width due to hidden fields

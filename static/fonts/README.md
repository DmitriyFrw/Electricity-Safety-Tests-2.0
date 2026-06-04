# Шрифты DejaVu (кириллица в PDF)

Файлы `DejaVuSans*.ttf` используются `app/pdf_service.py` для протоколов с кириллицей.

Лицензия: [DejaVu Fonts License](https://dejavu-fonts.github.io/License.html).

Установка:

```bash
./scripts/fetch-dejavu-fonts.sh
```

В Docker шрифты подтягиваются из `fonts-dejavu-core` и/или этого каталога при сборке образа.

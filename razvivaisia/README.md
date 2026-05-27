# Развивайся — статический макет (HTML)

Исходные HTML-прототипы интерфейса. Синхронизированы с React-приложением.

## Карта соответствия

| Макет (HTML) | React-маршрут | API |
|--------------|---------------|-----|
| `index.html` | `/cabinet` | `GET /api/dashboard` |
| `training.html` | `/training` | `GET /api/tests` |
| `training-test.html` | `/training/:testId` | `GET/POST /api/tests/:id/training` |
| `exam.html` | `/exam` | `GET /api/tests` |
| `exam-test.html` | `/exam/:testId` | exam session API |
| `documents.html` | `/manuals` | `GET /api/manuals` |

## Синхронизированные пути в проекте

| Источник | Назначение |
|----------|------------|
| `razvivaisia/css/*.css` | `frontend/src/styles/razvivaisia/*.css` |
| `razvivaisia/js/main.js` | `frontend/public/razvivaisia/main.js` + `frontend/src/hooks/useMobileNav.ts` |
| `razvivaisia/*.html` | `frontend/public/razvivaisia/*.html` (статические прототипы) |
| `assets/images/` | `frontend/public/razvivaisia/assets/images/` |

## Обновление стилей

После правок в `razvivaisia/css/` скопируйте файлы:

```bash
cp razvivaisia/css/*.css frontend/src/styles/razvivaisia/
```

React-специфичные стили (auth, мост классов) — в `frontend/src/styles/react-bridge.css`.

## Ассеты

- `logo.svg`, `hedgehog-avatar.svg`, `hedgehog-helmet.svg` — в `frontend/public/razvivaisia/assets/images/`
- Замените на финальные файлы из Figma при необходимости.

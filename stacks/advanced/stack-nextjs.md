# Stack: Next.js (App Router) + TypeScript

## Когда выбирать

Веб-продукты с UI: SaaS, лендинги с логикой, кабинеты. SSR/SEO из коробки, один репозиторий на фронт и лёгкий бэк (route handlers). Не выбирать: чистые API без UI (лишний вес), тяжёлый realtime (смотреть отдельный WS-сервис).

## Состав

- Next.js 15+ (App Router), TypeScript strict
- Tailwind CSS (токены стайлгайда → tailwind.config)
- Drizzle ORM или Prisma + PostgreSQL (Railway addon)
- Валидация: zod (обе стороны)
- Тесты: vitest (unit/integration), Playwright (E2E)

## Структура проекта

```
src/
  app/                  ← маршруты (App Router), только сборка страниц
  modules/<domain>/     ← модульный монолит: ui/, api/, model/, lib/ внутри модуля
  shared/               ← общие ui-компоненты, утилиты, конфиг
  i18n/                 ← словари и настройка локалей
```

## Конвенции

- Логика — в modules/<domain>, страницы в app/ только собирают модули; между модулями — через публичный index.ts модуля, не вглубь.
- Server Components по умолчанию; 'use client' — только где нужна интерактивность.
- Данные снаружи (формы, API, env) — через zod-схемы.
- Тесты рядом с кодом: `*.test.ts`; E2E — в `e2e/`.

## Команды

`npm run dev` · `npm run build` · `npm test` · `npx playwright test` · `npm run lint` · миграции — по выбранной ORM (`npx drizzle-kit …` / `npx prisma migrate …`)

## Деплой на Railway

- Builder: Nixpacks определяет Next.js сам; start — `next start -p $PORT` (порт — из env!).
- Healthcheck: route handler `src/app/health/route.ts` → 200 + проверка коннекта к БД.
- Переменные: DATABASE_URL (Railway Postgres), NEXT_PUBLIC_* — только несекретное (попадает в бандл!).

## i18n

next-intl: словари в src/i18n/<locale>.json, все строки UI через t(), локаль — сегмент маршрута `[locale]`. Закладывать с M1, если мультиязычность возможна.

## Грабли

_(пополняется из проектов: дата — проект — что случилось — как избегать)_

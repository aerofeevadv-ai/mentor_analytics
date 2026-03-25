# Инструкция: Настройка OAuth для YouTube Data API v3

> Эту инструкцию выполняет Claude Chrome (browser automation).
> Цель: получить OAuth 2.0 credentials (client_id + client_secret) для записи в YouTube API (обновление тегов, описаний видео).

---

## Предварительные условия2

- Открыт браузер Chrome с расширением Claude in Chrome
- Пользователь залогинен в Google-аккаунт, привязанный к YouTube-каналу @analytic_offers
- YouTube Data API v3 уже включён в проекте Google Cloud (API-ключ для чтения работает)

---

## Шаг 0: Определить проект

1. Перейти на https://console.cloud.google.com/
2. Посмотреть, какой проект выбран в верхнем меню (project selector)
3. Если проектов несколько — найти тот, где уже включён YouTube Data API v3
4. Запомнить название проекта — все дальнейшие шаги выполняются в нём

---

## Шаг 1: Настроить OAuth Consent Screen

1. Перейти на https://console.cloud.google.com/apis/credentials/consent
2. Если consent screen уже настроен — перейти к Шагу 2
3. Если нет — настроить:

### 1.1 Выбор типа приложения
- Выбрать **External** (если Internal недоступен)
- Нажать **Create**

### 1.2 Заполнение формы App Information
| Поле | Значение |
|---|---|
| App name | `Mentor Analytics YouTube` |
| User support email | email аккаунта (выбрать из дропдауна) |
| Developer contact email | тот же email |

- Остальные поля (logo, app domain, authorized domains) — оставить пустыми
- Нажать **Save and Continue**

### 1.3 Scopes
- Нажать **Add or Remove Scopes**
- В поиске ввести `youtube`
- Выбрать scope: `https://www.googleapis.com/auth/youtube` (полный доступ YouTube)
- Если нет в списке, вручную вписать в поле "Manually add scopes": `https://www.googleapis.com/auth/youtube`
- Нажать **Update** → **Save and Continue**

### 1.4 Test Users
- Нажать **Add Users**
- Ввести email Google-аккаунта владельца канала
- Нажать **Add** → **Save and Continue**

### 1.5 Summary
- Проверить данные → **Back to Dashboard**

---

## Шаг 2: Создать OAuth 2.0 Client ID

1. Перейти на https://console.cloud.google.com/apis/credentials
2. Нажать **+ CREATE CREDENTIALS** (кнопка вверху)
3. Выбрать **OAuth client ID**

### 2.1 Заполнение формы
| Поле | Значение |
|---|---|
| Application type | **Desktop app** |
| Name | `mentor-analytics-youtube-oauth` |

4. Нажать **Create**

### 2.2 Получить credentials
- Появится модальное окно с **Client ID** и **Client Secret**
- **Скопировать оба значения** и показать пользователю
- Также нажать **Download JSON** — это файл `client_secret_*.json`

---

## Шаг 3: Подтверждение результата

После выполнения сообщить пользователю:

```
OAuth credentials созданы:
- Client ID: [значение]
- Client Secret: [значение]
- JSON скачан: [имя файла]

Следующий шаг: запустить скрипт авторизации для получения refresh_token.
```

---

## Важные замечания

- **Тип приложения — Desktop app**, не Web application. Для Desktop app не нужен redirect URI на сервере, авторизация проходит через localhost.
- **Consent screen в статусе Testing** — это нормально. Для личного использования (1 аккаунт) публикация не нужна. В Testing режиме refresh_token истекает через 7 дней — после получения токена можно поставить статус Production (без верификации Google, если < 100 пользователей).
- **НЕ удалять существующий API Key** — он используется для read-операций и продолжит работать.

---

## Что делать после (вне scope этой инструкции)

После получения client_secret JSON нужно:
1. Сохранить JSON в безопасное место (НЕ коммитить в git)
2. Запустить скрипт авторизации (Python + google-auth-oauthlib) для получения access_token + refresh_token
3. Использовать токены в скрипте массовой простановки тегов

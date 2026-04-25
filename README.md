# IT-BE Django REST Skeleton

Backend skeleton theo Django RESTful API, modular theo domain apps, code-first voi MySQL.

## 1. Tao va kich hoat .venv (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Cai dependency

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

## 3. Cau hinh env

```powershell
Copy-Item .env.example .env
```

Cap nhat thong tin MySQL trong `.env`.

## 4. Migrate

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
```

## 5. Run server

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

## API co ban

## Auth JWT flow

IT-BE hien da ho tro flow auth day du bang JWT. FE co the dung cac endpoint sau:

### 1. Dang ky

```http
POST /api/auth/register/
```

Body:

```json
{
	"email": "candidate@example.com",
	"password": "Secret123!",
	"vai_tro": "ung_vien"
}
```

### 2. Dang nhap

```http
POST /api/auth/login/
```

Body:

```json
{
	"email": "candidate@example.com",
	"password": "Secret123!"
}
```

Response:

```json
{
	"access": "...",
	"refresh": "...",
	"token_type": "Bearer"
}
```

### 3. Lay user hien tai

```http
GET /api/auth/me/
Authorization: Bearer <access>
```

### 4. Refresh access token

```http
POST /api/auth/token/refresh/
```

Body:

```json
{
	"refresh": "..."
}
```

### 5. Dang xuat

```http
POST /api/auth/logout/
Authorization: Bearer <access>
```

Body:

```json
{
	"refresh": "..."
}
```

### Luu y

- Access token dung de goi endpoint protected.
- Refresh token dung de lay access moi va se bi blacklist sau logout.
- Endpoint cu van ton tai de backward compatibility:
  - `POST /api/auth/token/`
  - `POST /api/auth/token/refresh/`
  - `POST /api/accounts/users/`

## Test token endpoint (khong can login)

De test nhanh cac endpoint can JWT khi sprint chua co login/logout, co the dung endpoint:

```http
POST /api/auth/test-token/
```

Co the truyen role trong body de mint token theo role mong muon:

```json
{
	"vai_tro": "ung_vien"
}
```

Hoac:

```json
{
	"role": "cong_ty"
}
```

Role hop le: `ung_vien`, `cong_ty`, `admin`.

Response:

```json
{
	"access": "...",
	"refresh": "...",
	"token_type": "Bearer",
	"user": {
		"id": 1,
		"email": "sprint-test@example.com",
		"vai_tro": "cong_ty"
	}
}
```

Su dung access token cho API protected:

```http
Authorization: Bearer <access>
```

Bien moi truong lien quan:

- `TEST_TOKEN_ENDPOINT_ENABLED` (mac dinh: `true`)
- `TEST_TOKEN_EMAIL` (mac dinh: `sprint-test@example.com`)
- `TEST_TOKEN_ROLE` (mac dinh: `cong_ty`)
- `TEST_TOKEN_PASSWORD` (mac dinh: `test-token-password`)
- `TEST_TOKEN_SHARED_SECRET` (mac dinh: rong, neu dat thi request phai gui header `X-Test-Token-Secret`)


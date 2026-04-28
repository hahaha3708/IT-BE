# API Contract - Auth JWT V1

## 1. Common Rules
- Base path: `/api/auth`
- Content type: `application/json`
- Token type: `Bearer`
- Access token su dung cho protected APIs qua header:
  - `Authorization: Bearer <access_token>`

## 2. Endpoint Scope
Contract nay bao gom cac endpoint:
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`
- `POST /api/auth/logout/`

## 3. POST /api/auth/register/
Dang ky tai khoan moi.

### Request Body
```json
{
  "email": "candidate@example.com",
  "password": "Secret123!",
  "vai_tro": "ung_vien"
}
```

### Field Rules
- `email` (required, email, unique)
- `password` (required, string, theo Django password validators)
- `vai_tro` (required, enum)
  - `ung_vien`
  - `cong_ty`
  - `admin`

### Success Response 201
```json
{
  "id": 101,
  "email": "candidate@example.com",
  "vai_tro": "ung_vien",
  "tao_luc": "2026-04-22T08:10:00Z"
}
```

### Validation Error 400
```json
{
  "error": "bad_request",
  "details": {
    "password": ["This password is too common."]
  }
}
```

### Conflict 409 (email da ton tai)
```json
{
  "error": "conflict",
  "message": "Email already exists"
}
```

## 4. POST /api/auth/login/
Dang nhap bang email va password, tra JWT pair.

### Request Body
```json
{
  "email": "candidate@example.com",
  "password": "Secret123!"
}
```

### Success Response 200
```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>",
  "token_type": "Bearer"
}
```

### Unauthorized 401
```json
{
  "error": "unauthorized",
  "message": "Invalid credentials"
}
```

## 5. POST /api/auth/token/refresh/
Doi refresh token lay access token moi.

### Request Body
```json
{
  "refresh": "<jwt_refresh>"
}
```

### Success Response 200
```json
{
  "access": "<new_jwt_access>"
}
```

### Unauthorized 401
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired refresh token"
}
```

## 6. GET /api/auth/me/
Lay thong tin user hien tai.

### Header
- `Authorization: Bearer <access_token>`

### Success Response 200
```json
{
  "id": 101,
  "email": "candidate@example.com",
  "vai_tro": "ung_vien",
  "is_active": true
}
```

### Unauthorized 401
```json
{
  "error": "unauthorized",
  "message": "Authentication credentials were not provided"
}
```

## 7. POST /api/auth/logout/
Dang xuat bang cach blacklist refresh token.

### Request Body
```json
{
  "refresh": "<jwt_refresh>"
}
```

### Header
- `Authorization: Bearer <access_token>`

### Success Response 200
```json
{
  "message": "Logged out successfully"
}
```

### Unauthorized 401
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired refresh token"
}
```

## 8. Auth/Error Contract

### 400 Bad Request
```json
{
  "error": "bad_request",
  "details": {
    "field_name": "validation message"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Missing or invalid JWT"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### 409 Conflict
```json
{
  "error": "conflict",
  "message": "Duplicate resource"
}
```

### 429 Too Many Requests
```json
{
  "error": "too_many_requests",
  "message": "Request limit exceeded"
}
```

## 9. Backward Compatibility Notes
- Van giu endpoint cu de tranh break he thong hien tai:
  - `POST /api/auth/token/`
  - `POST /api/auth/token/refresh/`
  - `POST /api/accounts/users/`
- FE moi nen uu tien tich hop contract auth nay.

## 10. FE-BE Integration Notes
- FE can luu ca `access` va `refresh` token.
- Khi access token het han, FE goi `POST /api/auth/token/refresh/` de lay access moi.
- Neu refresh token khong hop le hoac het han, FE chuyen ve man hinh login.
- FE khong nen phu thuoc vao cac field ngoai contract.

# API

## faceid-service (port 5001)
- `POST /api/encode-face` form-data `file`: trả `{ "embedding": [float]*128 }`
- `POST /api/compare-faces` json `{ "emb1": [...], "emb2": [...] }`: trả `{ "distance": float, "match": bool }`

## user-service (port 5002)
- `POST /api/register-face` form `username`, file `file`
- `POST /api/login-face` form `username`, file `file`

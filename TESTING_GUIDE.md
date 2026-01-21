# 🧪 Testing Guide - Contractify Backend

Quick verification that all 51 endpoints work correctly.

## Prerequisites

```bash
# Start the server
uvicorn app.main:app --reload --port 3000

# Or use Python directly
python -m app.main
```

## Authentication

For testing, use dev tokens (no Firebase setup needed):

```bash
# Dev token format: dev_userId_email
AUTH_TOKEN="dev_123_test@example.com"
```

---

## 🔍 Health Checks

```bash
# Root health
curl http://localhost:3000/health

# API health
curl http://localhost:3000/api/health
```

**Expected:** `{"status":"healthy","version":"1.0.0"}`

---

## 👤 Users Module (6 endpoints)

```bash
# Get current user profile
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/users/me

# Update profile
curl -X PATCH http://localhost:3000/api/users/me \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Juan","lastName":"Pérez"}'

# Get sessions
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/users/me/sessions

# Update preferences
curl -X PATCH http://localhost:3000/api/users/me/preferences \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"theme":"dark","language":"es"}'
```

---

## 📄 Contracts Module (19 endpoints)

```bash
# Create contract
curl -X POST http://localhost:3000/api/contracts \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Contrato de Prueba",
    "templateId":"tpl_arrendamiento_v1",
    "contractType":"ARRENDAMIENTO_VIVIENDA"
  }'

# List contracts
curl -H "Authorization: Bearer dev_123_test@example.com" \
  "http://localhost:3000/api/contracts?page=1&pageSize=10"

# Get contract stats
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/stats

# Get recent contracts
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/recent

# Get pending contracts
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/pending

# Get contract details (replace CONTRACT_ID)
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID

# Update contract content
curl -X PATCH http://localhost:3000/api/contracts/CONTRACT_ID/content \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"content":"<h1>Updated Content</h1>","source":"USER"}'

# Get versions
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID/versions

# Update status
curl -X PATCH http://localhost:3000/api/contracts/CONTRACT_ID/status \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"status":"GENERATED"}'

# Get valid transitions
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID/transitions

# Get history
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID/history

# Add party
curl -X POST http://localhost:3000/api/contracts/CONTRACT_ID/parties \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "role":"GUEST",
    "name":"María López",
    "email":"maria@example.com",
    "order":2
  }'

# Get parties
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID/parties

# Duplicate contract
curl -X POST http://localhost:3000/api/contracts/CONTRACT_ID/duplicate \
  -H "Authorization: Bearer dev_123_test@example.com"

# Delete contract
curl -X DELETE http://localhost:3000/api/contracts/CONTRACT_ID \
  -H "Authorization: Bearer dev_123_test@example.com"
```

---

## 📋 Templates Module (4 endpoints)

```bash
# List templates
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/templates

# Get template by ID
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/templates/tpl_arrendamiento_v1

# List contract types
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/types

# Get type schema
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/types/ARRENDAMIENTO_VIVIENDA/schema
```

---

## 🤖 AI Module (4 endpoints)

```bash
# Validate input
curl -X POST http://localhost:3000/api/ai/validate-input \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractType":"ARRENDAMIENTO_VIVIENDA",
    "inputs":{"arrendador_nombre":"Juan","arrendatario_nombre":"María"}
  }'

# Generate contract
curl -X POST http://localhost:3000/api/ai/generate-contract \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "templateId":"tpl_arrendamiento_v1",
    "contractType":"ARRENDAMIENTO_VIVIENDA",
    "jurisdiction":"CO",
    "inputs":{
      "arrendador_nombre":"Juan Pérez",
      "arrendador_cedula":"123456789",
      "arrendatario_nombre":"María López",
      "arrendatario_cedula":"987654321",
      "direccion":"Calle 123 #45-67",
      "ciudad":"Bogotá",
      "canon_mensual":1500000,
      "duracion_meses":12,
      "fecha_inicio":"2026-02-01"
    }
  }'

# Regenerate with feedback
curl -X POST http://localhost:3000/api/ai/regenerate \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "feedback":"Agregar cláusula sobre mantenimiento",
    "preserveStructure":true
  }'

# Get job status (if async)
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/ai/jobs/JOB_ID
```

---

## 📑 Documents Module (4 endpoints)

```bash
# Generate PDF (returns job)
curl -X POST http://localhost:3000/api/documents/generate-pdf \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"contractId":"CONTRACT_ID","includeAuditPage":true}'

# Get job status
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/documents/jobs/JOB_ID

# Download document
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/documents/DOCUMENT_ID/download \
  --output contract.pdf

# Verify document
curl -X POST http://localhost:3000/api/documents/DOCUMENT_ID/verify \
  -H "Authorization: Bearer dev_123_test@example.com"
```

---

## ✍️ Signatures Module (7 endpoints)

```bash
# Create signature token
curl -X POST http://localhost:3000/api/signatures/create-token \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "partyId":"PARTY_ID",
    "expiresInMinutes":1440
  }'

# Validate token (PUBLIC - no auth)
curl "http://localhost:3000/api/signatures/validate-token?token=TOKEN_HERE"

# Sign as authenticated user
curl -X POST http://localhost:3000/api/signatures/sign \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "partyId":"PARTY_ID",
    "evidence":{
      "ipAddress":"192.168.1.1",
      "userAgent":"Mozilla/5.0",
      "geolocation":"Bogotá, Colombia"
    }
  }'

# Sign as guest (PUBLIC - no auth)
curl -X POST http://localhost:3000/api/signatures/sign-guest \
  -H "Content-Type: application/json" \
  -d '{
    "token":"TOKEN_HERE",
    "evidence":{
      "ipAddress":"192.168.1.1",
      "userAgent":"Mozilla/5.0"
    }
  }'

# Get contract signatures
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/contracts/CONTRACT_ID/signatures

# Store evidence
curl -X POST http://localhost:3000/api/signatures/SIGNATURE_ID/evidence \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"ipAddress":"192.168.1.1","userAgent":"Mozilla/5.0"}'

# Download certificate
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/signatures/SIGNATURE_ID/certificate \
  --output certificate.pdf
```

---

## 📧 Notifications Module (5 endpoints)

```bash
# Send invitation
curl -X POST http://localhost:3000/api/notifications/send-invitation \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "partyId":"PARTY_ID",
    "message":"Por favor firma el contrato"
  }'

# Get templates
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/notifications/templates

# Cancel invitation
curl -X POST http://localhost:3000/api/notifications/invitations/INVITATION_ID/cancel \
  -H "Authorization: Bearer dev_123_test@example.com"

# Resend invitation
curl -X POST http://localhost:3000/api/notifications/invitations/INVITATION_ID/resend \
  -H "Authorization: Bearer dev_123_test@example.com"

# Schedule reminder
curl -X POST http://localhost:3000/api/notifications/reminders \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "contractId":"CONTRACT_ID",
    "partyId":"PARTY_ID",
    "scheduleAt":"2026-02-01T10:00:00Z"
  }'
```

---

## 📊 Audit Module (2 endpoints)

```bash
# Get audit trail
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/audit/contracts/CONTRACT_ID/trail

# Export audit trail
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/audit/contracts/CONTRACT_ID/export \
  --output audit.pdf
```

---

## 🎯 Complete Flow Test

```bash
# 1. Create contract
CONTRACT_ID=$(curl -s -X POST http://localhost:3000/api/contracts \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Contract","templateId":"tpl_arrendamiento_v1","contractType":"ARRENDAMIENTO_VIVIENDA"}' \
  | jq -r '.id')

echo "Contract created: $CONTRACT_ID"

# 2. Generate content with AI
curl -X POST http://localhost:3000/api/ai/generate-contract \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d "{
    \"contractId\":\"$CONTRACT_ID\",
    \"templateId\":\"tpl_arrendamiento_v1\",
    \"contractType\":\"ARRENDAMIENTO_VIVIENDA\",
    \"inputs\":{
      \"arrendador_nombre\":\"Juan\",
      \"arrendatario_nombre\":\"María\",
      \"direccion\":\"Calle 123\",
      \"ciudad\":\"Bogotá\",
      \"canon_mensual\":1500000,
      \"duracion_meses\":12
    }
  }"

# 3. Add parties
curl -X POST http://localhost:3000/api/contracts/$CONTRACT_ID/parties \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"role":"HOST","name":"Juan","email":"juan@example.com","order":1}'

# 4. Update status to SIGNING
curl -X PATCH http://localhost:3000/api/contracts/$CONTRACT_ID/status \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"status":"SIGNING"}'

# 5. Get audit trail
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/audit/contracts/$CONTRACT_ID/trail

echo "✅ Flow completed successfully!"
```

---

## 🔍 Verification Checklist

- [ ] Health checks respond
- [ ] User profile creation works
- [ ] Contract CRUD operations work
- [ ] Templates list correctly
- [ ] AI generation produces content
- [ ] PDF generation returns job ID
- [ ] Signatures can be created
- [ ] Notifications send successfully
- [ ] Audit trail logs events
- [ ] Public endpoints work without auth
- [ ] Protected endpoints require auth

---

## 📚 Swagger UI

Visit: http://localhost:3000/api/docs

Try all endpoints interactively with the built-in OpenAPI UI.

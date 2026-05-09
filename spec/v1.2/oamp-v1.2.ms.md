# Protokol Memori Ejen Terbuka — Versi 1.2.0

**Status:** Stabil  
**Tarikh:** 2026-05-09  
**Pengarang:** Jonathan Conway (Deep Thinking)  
**Menggantikan:** Tiada — memperluas v1.0.0 dan v1.1.0 secara tambahan  
**Repositori:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstrak

OAMP v1.2 adalah versi minor **tambahan ketat** ke atas v1.0.0 dan ciri draf v1.1 yang pilihan. Ia menstandardkan bentuk mudah alih untuk:

- metadata memori yang dikawal pada `KnowledgeEntry`,
- provenance pelbagai sumber yang lebih kaya pada `KnowledgeEntry`,
- pengiklanan kemampuan tadbir pada `GET /v1/capabilities`, dan
- kunci penapis yang peka terhadap tadbir untuk permukaan carian dan penstriman.

v1.2 secara sengaja **tidak** menstandardkan dokumen hasil yang ditahan atau disunting. Semantik tersebut memerlukan sama ada sampul respons baru atau perubahan yang merosakkan kepada kontrak `KnowledgeEntry`, jadi ia secara jelas ditangguhkan kepada trek reka bentuk v2.0 yang berasingan.

Kata kunci "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", dan "OPTIONAL" dalam dokumen ini harus ditafsirkan seperti yang diterangkan dalam [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Hubungan dengan v1.0 dan v1.1

v1.2 menggunakan semula semua skema, titik akhir, keperluan, dan semantik v1.0, ditambah model kemampuan v1.1 yang pilihan, tanpa mengubah sebarang medan yang diperlukan.

Satu-satunya penambahan baru pada tahap wire adalah:

- OPTIONAL `governance` pada `KnowledgeEntry`
- OPTIONAL `provenance` pada `KnowledgeEntry`
- OPTIONAL `capabilities.governance` pada `GET /v1/capabilities`
- OPTIONAL kunci penapis yang peka terhadap tadbir

Dokumen SHOULD menetapkan `oamp_version` kepada `"1.2.0"` apabila mereka menggunakan medan yang hanya ada dalam v1.2. Dokumen yang hanya menggunakan medan v1.0 MAY terus menggunakan `"1.0.0"` untuk kebolehpindahan maksimum.

---

## 2. Pembahagian Skop

### 2.1 Distandardkan dalam v1.2

- metadata memori yang dikawal yang mudah alih
- provenance yang lebih kaya yang mudah alih
- penemuan kemampuan untuk sokongan memori yang dikawal
- penapisan yang peka terhadap tadbir yang pilihan

### 2.2 Ditangguhkan secara jelas kepada v2.0

- dokumen hasil yang ditahan atau disunting yang distandardkan
- set hasil campuran yang mengandungi entri yang boleh dilihat dan stub yang ditahan
- muatan acara aliran untuk pengetahuan yang ditahan
- semantik `withholding_reason` yang mudah alih
- bahasa dasar polisi pengesahan silang-backend yang distandardkan

Pembahagian ini adalah normatif untuk draf v1.2. Pelaksanaan MUST NOT mendakwa bahawa stub yang ditahan atau disunting adalah distandardkan oleh v1.2.

---

## 3. Penambahan `KnowledgeEntry`

### 3.1 `governance` Pilihan

`KnowledgeEntry` mendapat objek `governance` yang OPTIONAL:

```json
{
  "governance": {
    "sensitivity_class": "confidential",
    "labels": ["finance", "hr"],
    "handling": {
      "retrieval": "governed",
      "export": "governed",
      "stream": "governed"
    }
  }
}
```

#### Medan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `governance` | objek | MAY | Metadata memori yang dikawal yang standard |
| `governance.sensitivity_class` | string | MUST jika `governance` ada | Salah satu daripada `public`, `internal`, `confidential`, `restricted` |
| `governance.labels` | array of string | MAY | Label tadbir yang ditakrifkan oleh backend atau penyewa |
| `governance.handling` | objek | MAY | Petunjuk pengendalian khusus permukaan |
| `governance.handling.retrieval` | string | MAY | `governed` atau `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` atau `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` atau `ungoverned` |

Objek `governance` adalah deskriptif. Ia bukan enjin polisi yang mudah alih.

### 3.2 `provenance` Pilihan

`KnowledgeEntry` mengekalkan objek `source` yang DITUNTUT dan menambah objek `provenance` yang lebih kaya yang OPTIONAL:

```json
{
  "source": {
    "session_id": "sess-42",
    "timestamp": "2026-05-07T10:00:00Z"
  },
  "provenance": {
    "sources": [
      {
        "session_id": "sess-42",
        "timestamp": "2026-05-07T10:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-3"
      },
      {
        "session_id": "sess-43",
        "timestamp": "2026-05-08T09:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-7"
      }
    ],
    "derived": true
  }
}
```

#### Medan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `provenance` | objek | MAY | Metadata keturunan yang diperluas |
| `provenance.sources` | array | MUST jika `provenance` ada | Senarai bukti/sumber yang teratur |
| `provenance.sources[].session_id` | string | MUST | Pengenal sesi sumber |
| `provenance.sources[].timestamp` | string | MUST | Masa pengambilan ISO 8601 |
| `provenance.sources[].agent_id` | string | MAY | Pengenal ejen sumber |
| `provenance.sources[].turn_id` | string | MAY | Pengenal tempatan turn/pesanan |
| `provenance.derived` | boolean | MAY | Sama ada entri ini disintesis daripada pelbagai sumber |

Medan `source` yang sedia ada kekal sebagai kontrak provenance minimum dan MUST masih ada.

---

## 4. Penambahan Kemampuan

v1.2 memperluas respons `GET /v1/capabilities` v1.1 dengan objek `capabilities.governance` yang OPTIONAL:

```json
{
  "oamp_version": "1.2.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false
    }
  }
}
```

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `governance.supported` | boolean | MUST jika `governance` ada | Backend memahami medan tadbir yang distandardkan |
| `governance.sensitivity_classes` | array of string | MUST | Kelas yang diterima oleh backend |
| `governance.labels_supported` | boolean | MUST | Sama ada label bebas disimpan dan dipelihara |
| `governance.extended_provenance_supported` | boolean | MUST | Sama ada `provenance` disimpan dan dipelihara |
| `governance.withheld_stub_support` | boolean | MUST | Sama ada backend mempunyai sebarang tingkah laku ditahan yang tidak standard |

`withheld_stub_support` adalah maklumat sahaja dalam v1.2 dan MUST NOT dibaca sebagai jaminan format hasil yang mudah alih.

---

## 5. Kunci Penapis Peka Terhadap Tadbir

Backend yang sudah menyokong penapis pertanyaan atau penapis langganan penstriman MAY mengiklankan dan menerima kunci peka terhadap tadbir yang OPTIONAL ini:

| Kunci | Jenis | Semantik |
|-----|------|-----------|
| `sensitivity_class` | array of string | Padankan entri yang `governance.sensitivity_class` ada dalam set |
| `governance_label` | array of string | Padankan entri yang mengandungi sekurang-kurangnya satu label tadbir yang disenaraikan |

Untuk titik akhir carian REST, ini MAY muncul sebagai parameter pertanyaan berulang. Untuk penstriman, ini MAY muncul dalam pengiklanan `streaming.filter_keys` dan dalam muatan langganan.

Backend yang tidak mengindeks metadata tadbir MAY menolak atau mengabaikan kunci ini, tetapi MUST mengiklankan sokongan dengan tepat dalam kemampuan.

---

## 6. Peraturan Keserasian

### 6.1 Backend v1.2

- MUST menerima dokumen v1.0 dan v1.1.
- MUST memelihara `governance` dan `provenance` apabila disokong.
- MUST terus bertoleransi terhadap pengembangan metadata khusus vendor yang tidak diketahui.

### 6.2 Klien v1.0 dan v1.1

- MAY mengabaikan `governance` dan `provenance` jika mereka tidak memahaminya.
- MUST NOT menganggap semantik hasil yang ditahan atau disunting hanya berdasarkan rentetan versi v1.2.

### 6.3 Import dan eksport

- Backend yang menyokong memori yang dikawal SHOULD memelihara `governance` dan `provenance` yang distandardkan merentasi eksport dan import.
- Backend yang tidak menyokong memori yang dikawal SHOULD mendokumentasikan sama ada medan tersebut dipelihara secara tidak jelas atau dibuang.

---

## 7. Skema Dan Artifak OpenAPI

Draf v1.2 diwakili oleh:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

Artifak ini adalah tambahan ke atas `spec/v1/` dan tidak mengubah kontrak medan yang diperlukan v1.0.
# Protokol Memori Ejen Terbuka — Versi 1.3.0 (Draf)

**Status:** Draf (versi kecil yang dicadangkan)  
**Tarikh:** 2026-05-07  
**Pengarang:** Jonathan Conway (Deep Thinking)  
**Menggantikan:** Tiada — memperluas v1.0.0, v1.1.0, dan v1.2.0 secara tambahan  
**Repositori:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstrak

OAMP v1.3 adalah versi kecil yang **secara ketat tambahan** ke atas v1.0.0 dan ciri draf pilihan v1.1 dan v1.2. Ia menstandardkan lapisan **penguatkuasaan** untuk memori yang dikawal yang diperkenalkan secara deskriptif dalam v1.2.

v1.2 menstandardkan:

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- `provenance` yang lebih kaya
- penemuan kemampuan tadbir urus

v1.3 mendefinisikan apa yang mesti dilakukan oleh backend dengan bidang tersebut apabila beberapa ejen untuk pengguna yang sama mengakses backend yang sama. Ia menstandardkan:

- tuntutan pemberian ejen yang boleh dibawa
- konvensyen padanan label hierarki
- peraturan penapisan baca, tulis, import, eksport, dan aliran
- penyembunyian kewujudan pada permukaan ejen
- pengikatan identiti ejen kepada provenance
- penambahan log audit
- pengiklanan kemampuan untuk sokongan penguatkuasaan

v1.3 kekal **berdasarkan pengecualian**. Ia **tidak** menstandardkan dokumen hasil yang ditahan atau disunting yang boleh dibawa. Kerja itu ditangguhkan kepada trek v2.0 yang berasingan.

Kata kunci "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", dan "OPTIONAL" dalam dokumen ini harus ditafsirkan seperti yang diterangkan dalam [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Hubungan Dengan Versi Sebelumnya

v1.3 menggunakan semula setiap skema v1.0, titik akhir, keperluan, dan peraturan semantik, ditambah model kemampuan v1.1 yang pilihan dan model metadata memori yang dikawal v1.2 yang tambahan.

Satu-satunya penambahan baru pada tahap wire dalam v1.3 adalah:

- OPTIONAL `capabilities.governance.enforcement` pada `GET /v1/capabilities`
- format tuntutan pemberian ejen yang boleh dibawa untuk tuntutan JWT atau `OAMP-Grant`
- tingkah laku backend normatif yang menggunakan bidang `governance` v1.2 yang sedia ada

v1.3 memperkenalkan **tiada bidang `KnowledgeEntry` baru** dan **tiada bidang `KnowledgeStore` baru**.

Dokumen yang hanya menggunakan bidang entry/store v1.0-v1.2 boleh terus menggunakan `"1.2.0"` untuk `oamp_version`. Dokumen dan respons yang ingin mengiklankan barisan draf v1.3 boleh menggunakan `"1.3.0"`.

---

## 2. Pembahagian Skop

### 2.1 Standardized Dalam v1.3

- tuntutan pemberian per-ejen yang boleh dibawa
- semantik penguatkuasaan label tadbir urus hierarki
- makna operasi untuk petunjuk pengendalian tadbir urus v1.2
- penapisan baca
- penolakan tulis
- pengiraan penolakan import
- penapisan eksport dan `oamp_export_full`
- penapisan aliran pada permukaan v1.1
- penyembunyian kewujudan pada permukaan ejen
- pengikatan provenance kepada `oamp_agent_id`
- pengiklanan kemampuan penguatkuasaan tadbir urus
- nama tindakan audit untuk acara pemberian dan skop

### 2.2 Ditangguhkan secara eksplisit kepada v2.0

- dokumen hasil yang ditahan atau disunting yang distandardkan
- set hasil campuran yang mengandungi entri yang boleh dilihat dan stub yang ditahan
- semantik `withholding_reason` yang boleh dibawa
- payload aliran yang secara eksplisit mewakili pengetahuan yang ditahan
- bahasa polisi pengesahan silang-backend yang boleh dibawa

Pelaksanaan **MUST NOT** mendakwa bahawa v1.3 menstandardkan dokumen stub yang ditahan atau disunting.

---

## 3. Penggunaan Semula Metadata Tadbir Urus v1.2

v1.3 menambah **tiada bidang tadbir urus peringkat entry baru**. Sebaliknya, ia menjadikan bidang v1.2 beroperasi.

### 3.1 `governance.sensitivity_class`

Enum v1.2 adalah teratur:

`public < internal < confidential < restricted`

Tuntutan pemberian ejen membawa `oamp_sensitivity_max`. Entri yang kelas `sensitivity_class` berkesan melebihi siling pemberian akan ditapis atau ditolak.

Apabila `governance` tidak ada, kelas berkesan adalah `internal` untuk tujuan penguatkuasaan.

### 3.2 `governance.labels`

v1.3 memperkenalkan konvensyen label hierarki yang digunakan oleh penguatkuasaan.

- Sebuah label **SHOULD** menjadi laluan ASCII huruf kecil bertitik yang sepadan dengan
  `^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$`
- Padanan awalan hierarki terpakai
- Sebuah pemberian untuk `health` sepadan dengan `health.condition` dan
  `health.condition.diagnosis`

Label tahap atas yang terpelihara untuk interoperabiliti merentasi vendor:

- `identity`
- `location`
- `health`
- `finance`
- `relationships`
- `work`
- `preferences`
- `creative`
- `beliefs`
- `behaviour`

Panjangan khusus vendor **SHOULD** berada di bawah `x.<vendor>.<...>`.

Label yang tidak sepadan dengan konvensyen hierarki kekal sebagai label deskriptif v1.2 yang sah, tetapi backend yang menguatkuasakan v1.3 **SHOULD** menganggapnya sebagai nilai padanan tepat yang legap.

Apabila `governance.labels` tidak ada atau kosong, set label berkesan adalah `["behaviour"]` untuk tujuan penguatkuasaan.

### 3.3 `governance.handling`

Petunjuk `handling` v1.2 menjadi beban dalam v1.3:

- `retrieval: "governed"` bermakna laluan baca **MUST** menggunakan penapisan pemberian
- `retrieval: "ungoverned"` mengecualikan entri daripada penapisan laluan baca
- `export: "governed"` bermakna laluan eksport **MUST** menggunakan penapisan pemberian
- `export: "ungoverned"` mengecualikan entri daripada penapisan laluan eksport
- `stream: "governed"` bermakna laluan penstriman v1.1 **MUST** menggunakan penapisan pemberian
- `stream: "ungoverned"` mengecualikan entri daripada penapisan aliran

Apabila `governance` hadir dan nilai pengendalian tidak dinyatakan, default berkesan adalah `governed` untuk permukaan itu.

---

## 4. Tuntutan Pemberian Ejen

### 4.1 Bentuk tuntutan JWT

Apabila pengesahan pembawa menggunakan JWT, token membawa tuntutan tambahan ini:

```json
{
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels": ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "oamp_export_full": false,
  "exp": 1746662400
}
```

| Tuntutan | Keperluan | Penerangan |
|----------|-----------|------------|
| `oamp_agent_id` | MUST | Pengenal pasti stabil untuk ejen yang memanggil |
| `oamp_grant_id` | MUST | Pengenal pasti stabil untuk instans pemberian |
| `oamp_read_labels` | MUST | Label yang boleh dibaca oleh ejen |
| `oamp_write_labels` | MUST | Label yang boleh ditulis oleh ejen |
| `oamp_sensitivity_max` | MUST | Kelas sensitiviti yang boleh dibaca/ditulis tertinggi |
| `oamp_export_full` | MAY | Sama ada eksport penuh yang tidak ditapis dibenarkan |

`oamp_read_labels` yang kosong bermakna baca-tiada.

### 4.2 Header `OAMP-Grant`

Untuk penyebaran yang tidak menggunakan token pembawa JWT, objek tuntutan yang sama **MAY** disampaikan dalam header `OAMP-Grant`. Nilai header **MUST** menjadi JWS padat ke atas objek tuntutan.

### 4.3 Pengikatan Provenance

Apabila penulisan berlaku di bawah pemberian v1.3, backend **MUST** mengesahkan:

- `entry.source.agent_id == oamp_agent_id`, apabila `source.agent_id` hadir

Untuk entri dengan `provenance.sources[*].agent_id`, backend **SHOULD** mengesahkan setiap `agent_id` yang disenaraikan terhadap pemberian yang memanggil atau model kepercayaan tempatan mereka.

---

## 5. Peraturan Penguatkuasaan Backend

Backend yang mengiklankan `governance.enforcement.supported: true` **MUST** menggunakan peraturan ini.

### 5.1 Penapisan baca

Sebuah entri lulus bacaan yang dikawal hanya jika:

1. pengendalian pengambilan berkesan tidak dikecualikan, dan
2. sekurang-kurangnya satu label entri berkesan sepadan dengan beberapa label baca yang diberikan, dan
3. kelas sensitiviti berkesan adalah kurang daripada atau sama dengan
   `oamp_sensitivity_max`

Entri yang gagal **MUST NOT** muncul dalam:

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- respons carian
- `POST /v1/export`
- penghantaran aliran v1.1

### 5.2 Penyembunyian kewujudan

Entri yang di luar skop **MUST** disembunyikan pada permukaan ejen.

- `GET /v1/knowledge/{id}` **MUST** mengembalikan `404 Not Found`, bukan `403 Forbidden`,
  untuk id yang di luar skop
- entri yang ditapis **MUST NOT** menyumbang kepada jumlah respons

### 5.3 Penolakan tulis

`POST /v1/knowledge` **MUST** ditolak dengan `403 Forbidden` jika:

- label berkesan entri berada di luar pemberian tulis, atau
- kelas sensitiviti berkesan entri melebihi `oamp_sensitivity_max`, atau
- `source.agent_id` bertentangan dengan `oamp_agent_id`

### 5.4 Penolakan import

`POST /v1/import` **MUST** menolak entri yang melebihi pemberian tulis dan **MUST** mengira mereka dalam medan `rejected` respons import.

### 5.5 Penapisan eksport

`POST /v1/export` **MUST** mengembalikan hanya entri yang boleh dibaca di bawah pemberian, kecuali
`oamp_export_full` hadir dan dibenarkan di bawah pengesahan pengguna langsung.

### 5.6 Penapisan aliran

Jika sebuah backend menyokong penstriman v1.1, ia **MUST**:

- mengecualikan `knowledge_created` dan `knowledge_updated` untuk entri yang di luar skop
- mengecualikan `knowledge_deleted` untuk entri yang tidak dibenarkan dibaca oleh ejen

---

## 6. Penambahan Kemampuan

v1.3 memperluas blok kemampuan tadbir urus v1.2:

```json
{
  "oamp_version": "1.3.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false,
      "enforcement": {
        "supported": true,
        "spec_version": "1.3.0",
        "label_hierarchy": "dotted-prefix",
        "reserved_top_level_labels": [
          "identity", "location", "health", "finance",
          "relationships", "work", "preferences",
          "creative", "beliefs", "behaviour"
        ],
        "grant_transport": ["jwt-claims", "oamp-grant-header"],
        "existence_hiding": true,
        "stream_filtering": true,
        "export_full_supported": true
      }
    }
  }
}
```

| Medan | Jenis | Keperluan | Penerangan |
|-------|-------|-----------|------------|
| `enforcement.supported` | boolean | MUST jika `enforcement` hadir | Backend menggunakan peraturan penguatkuasaan v1.3 |
| `enforcement.spec_version` | string | MUST | Garis spesifikasi v1.3 yang dilaksanakan |
| `enforcement.label_hierarchy` | string | MUST | `dotted-prefix` untuk draf ini |
| `enforcement.reserved_top_level_labels` | array of string | MUST | Label tahap atas yang terpelihara untuk interoperabiliti |
| `enforcement.grant_transport` | array of string | MUST | Mekanisme pengangkutan pemberian yang disokong |
| `enforcement.existence_hiding` | boolean | MUST | Sama ada id yang di luar skop disembunyikan sebagai 404 |
| `enforcement.stream_filtering` | boolean | MUST | Sama ada aliran v1.1 ditapis |
| `enforcement.export_full_supported` | boolean | MUST | Sama ada tuntutan eksport penuh dihormati |

---

## 7. Penambahan Log Audit

Kosa kata tindakan audit mendapat:

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read` **MUST NOT** mencatat kandungan entri yang dilindungi dan **SHOULD** mengelakkan mencatat id entri yang ditapis pada permukaan ejen.

---

## 8. Peraturan Keserasian

### 8.1 Backend v1.3

- **MUST** terus menerima dokumen v1.0, v1.1, dan v1.2
- **MUST** memelihara `governance` dan `provenance` v1.2
- **MUST** mengiklankan sokongan penguatkuasaan dengan tepat

### 8.2 Klien v1.0-v1.2

- **MAY** mengabaikan blok `governance.enforcement` jika mereka tidak memahaminya
- **MUST NOT** menyimpulkan semantik hasil yang ditahan yang boleh dibawa dari string versi `1.3.0` sahaja

### 8.3 Token tanpa pemberian

Pada backend yang menguatkuasakan v1.3 untuk permukaan ejen, token yang tidak menunjukkan `oamp_read_labels` yang boleh digunakan **MUST** dianggap sebagai baca-tiada.

Penyebaran **MAY** masih menyediakan laluan pengesahan pengguna langsung yang berasingan di luar format pemberian yang boleh dibawa.

---

## 9. Skema Dan Artifak OpenAPI

Draf v1.3 diwakili oleh:

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

Skema entry dan store kekal tambahan ke atas v1.2. Novelti utama v1.3 adalah kontrak kemampuan penguatkuasaan dan tingkah laku backend normatif yang ditakrifkan dalam draf ini.
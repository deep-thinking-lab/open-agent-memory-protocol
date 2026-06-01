# Protokol Memori Ejen Terbuka — Versi 1.3.0 (Draf)

**Status:** Draf (versi kecil yang dicadangkan)  
**Tarikh:** 2026-05-07  
**Pengarang:** Jonathan Conway (Deep Thinking)  
**Menggantikan:** Tiada — memperluas v1.0.0, v1.1.0, dan v1.2.0 secara additive  
**Repositori:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstrak

OAMP v1.3 adalah versi kecil yang **secara ketat additive** ke atas v1.0.0 dan ciri draf pilihan v1.1 dan v1.2. Ia menstandardkan lapisan **penguatkuasaan** untuk memori yang dikawal yang diperkenalkan secara deskriptif dalam v1.2.

v1.2 menstandardkan:

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- `provenance` yang lebih kaya
- penemuan kemampuan tadbir urus

v1.3 mentakrifkan apa yang MESTI dilakukan oleh backend dengan medan tersebut apabila beberapa ejen untuk pengguna yang sama mengakses backend yang sama. Ia menstandardkan:

- tuntutan hak ejen yang boleh dibawa
- konvensyen pemadanan label hierarki
- peraturan penapisan baca, tulis, import, eksport, dan aliran
- penyembunyian kewujudan pada permukaan ejen
- pengikatan identiti ejen kepada provenance
- penambahan log audit
- pengiklanan kemampuan untuk sokongan penguatkuasaan

v1.3 kekal **berdasarkan pengecualian**. Ia **tidak** menstandardkan dokumen hasil yang ditahan atau disunting yang boleh dibawa. Kerja itu ditangguhkan kepada trek v2.0 yang berasingan.

Kata kunci "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", dan "OPTIONAL" dalam dokumen ini harus ditafsirkan seperti yang diterangkan dalam [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Hubungan Dengan Versi Sebelumnya

v1.3 menggunakan semula setiap skema, titik akhir, keperluan, dan peraturan semantik v1.0, ditambah model kemampuan v1.1 yang pilihan dan model metadata memori yang dikawal v1.2 yang additive.

Satu-satunya penambahan baru di peringkat wire dalam v1.3 adalah:

- PILIHAN `capabilities.governance.enforcement` pada `GET /v1/capabilities`
- format tuntutan hak ejen yang boleh dibawa untuk tuntutan JWT atau `OAMP-Grant`
- tingkah laku backend normatif yang menggunakan medan `governance` v1.2 yang sedia ada

v1.3 memperkenalkan **tiada medan `KnowledgeEntry` baru** dan **tiada medan `KnowledgeStore` baru**.

Dokumen yang hanya menggunakan medan entry/store v1.0-v1.2 BOLEH terus menggunakan `"1.2.0"` untuk `oamp_version`. Dokumen dan respons yang ingin mengiklankan barisan draf v1.3 BOLEH menggunakan `"1.3.0"`.

---

## 2. Pembahagian Skop

### 2.1 Distandardkan Dalam v1.3

- tuntutan hak ejen yang boleh dibawa
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
- nama tindakan audit untuk acara grant dan scope

### 2.2 Ditangguhkan secara eksplisit kepada v2.0

- dokumen hasil yang ditahan atau disunting yang distandardkan
- set hasil campuran yang mengandungi entri yang boleh dilihat dan stub yang ditahan
- semantik `withholding_reason` yang boleh dibawa
- payload aliran yang secara eksplisit mewakili pengetahuan yang ditahan
- bahasa dasar polisi pengesahan silang-backend yang boleh dibawa

Pelaksanaan MESTI TIDAK mendakwa bahawa v1.3 menstandardkan dokumen stub yang ditahan atau disunting.

---

## 3. Penggunaan Semula Metadata Tadbir Urus v1.2

v1.3 menambah **tiada medan tadbir urus peringkat entry baru**. Sebaliknya, ia menjadikan medan v1.2 beroperasi.

### 3.1 `governance.sensitivity_class`

Enum v1.2 adalah teratur:

`public < internal < confidential < restricted`

Tuntutan hak ejen membawa `oamp_sensitivity_max`. Entri yang kelas `sensitivity_class` berkesan melebihi siling grant akan ditapis atau ditolak.

Apabila `governance` tidak ada, kelas berkesan adalah `internal` untuk tujuan penguatkuasaan.

### 3.2 `governance.labels`

v1.3 memperkenalkan konvensyen label hierarki yang digunakan oleh penguatkuasaan.

- Sebuah label SHOULD menjadi laluan ASCII huruf kecil bertitik yang sepadan dengan
  `^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$`
- Pemadanan awalan hierarki terpakai
- Tuntutan untuk `health` sepadan dengan `health.condition` dan
  `health.condition.diagnosis`

Label tahap atas yang terpelihara untuk interoperabiliti silang-vendor:

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

Panjangan khusus vendor SHOULD berada di bawah `x.<vendor>.<...>`.

Label yang tidak sepadan dengan konvensyen hierarki kekal sebagai label deskriptif v1.2 yang sah, tetapi backend yang menguatkuasakan v1.3 SHOULD menganggapnya sebagai nilai pemadanan tepat yang legap.

Apabila `governance.labels` tidak ada atau kosong, set label berkesan adalah `["behaviour"]` untuk tujuan penguatkuasaan.

### 3.3 `governance.handling`

Petunjuk `handling` v1.2 menjadi beban dalam v1.3:

- `retrieval: "governed"` bermaksud laluan baca MESTI menggunakan penapisan grant
- `retrieval: "ungoverned"` mengecualikan entri daripada penapisan laluan baca
- `export: "governed"` bermaksud laluan eksport MESTI menggunakan penapisan grant
- `export: "ungoverned"` mengecualikan entri daripada penapisan laluan eksport
- `stream: "governed"` bermaksud laluan penstriman v1.1 MESTI menggunakan penapisan grant
- `stream: "ungoverned"` mengecualikan entri daripada penapisan aliran
- `mediation: "required"` bermaksud akses kepada entri memerlukan grant yang sah daripada
  penerbit mediasi yang dipercayai
- `mediation: "optional"` bermaksud tiada sekatan mediasi dinyatakan

Apabila `governance` ada dan nilai pengendalian diabaikan, default berkesan adalah `governed` untuk permukaan itu.

Apabila `mediation` diabaikan, default berkesan adalah `optional`.

---

## 4. Tuntutan Hak Ejen

### 4.1 Bentuk tuntutan JWT

Apabila pengesahan pembawa menggunakan JWT, token membawa tuntutan tambahan ini:

```json
{
  "iss": "governor",
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels": ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "oamp_export_full": false,
  "oamp_mediation_required": true,
  "oamp_task_id": "task-7",
  "oamp_context_id": "mission-3",
  "exp": 1746662400
}
```

| Tuntutan | Keperluan | Penerangan |
|----------|-----------|------------|
| `oamp_agent_id` | MUST | Pengenal pasti stabil untuk ejen yang memanggil |
| `oamp_grant_id` | MUST | Pengenal pasti stabil untuk instans grant |
| `oamp_read_labels` | MUST | Label yang boleh dibaca oleh ejen |
| `oamp_write_labels` | MUST | Label yang boleh ditulis oleh ejen |
| `oamp_sensitivity_max` | MUST | Kelas sensitiviti yang boleh dibaca/ditulis tertinggi |
| `oamp_export_full` | MAY | Sama ada eksport penuh yang tidak ditapis dibenarkan |
| `iss` | MUST untuk sumber yang memerlukan mediasi; jika tidak MAY | Pengenal pasti stabil bagi pihak yang mengeluarkan grant |
| `oamp_mediation_required` | MAY | Menandakan bahawa grant ini bertujuan untuk aliran yang dimediasi |
| `oamp_task_id` | MAY | Pengenal pasti unit kerja yang ditugaskan kepada ejen |
| `oamp_context_id` | MAY | Pengenal pasti pengelompokan legap di atas tugas |

`oamp_read_labels` yang kosong bermaksud baca-tiada.

### 4.2 Header `OAMP-Grant`

Untuk penyebaran yang tidak menggunakan token pembawa JWT, objek tuntutan yang sama BOLEH disampaikan dalam header `OAMP-Grant`. Nilai header MESTI menjadi JWS padat ke atas objek tuntutan.

### 4.3 Pengikatan provenance

Apabila penulisan berlaku di bawah grant v1.3, backend MESTI mengesahkan:

- `entry.source.agent_id == oamp_agent_id`, apabila `source.agent_id` ada

Untuk entri dengan `provenance.sources[*].agent_id`, backend SHOULD mengesahkan setiap `agent_id` yang disenaraikan terhadap grant yang memanggil atau model kepercayaan tempatan mereka.

Apabila penulisan berlaku di bawah grant v1.3.1 yang membawa `oamp_task_id` atau
`oamp_context_id`, backend SHOULD mencap nilai tersebut pada
`provenance.sources[*].task_id` dan `provenance.sources[*].context_id` untuk sumber yang dihasilkan oleh grant tersebut. Medan ini hanya atribusi deskriptif dan MESTI TIDAK meluaskan akses.

---

## 5. Peraturan Penguatkuasaan Backend

Backend yang mengiklankan `governance.enforcement.supported: true` MESTI menerapkan peraturan ini.

### 5.1 Penapisan baca

Sebuah entri lulus bacaan yang dikawal hanya jika:

1. pengendalian pengambilan berkesan tidak dikecualikan, dan
2. sekurang-kurangnya satu label entri berkesan sepadan dengan beberapa label baca yang diberikan, dan
3. kelas sensitiviti berkesan kurang daripada atau sama dengan
   `oamp_sensitivity_max`

Entri yang gagal MESTI TIDAK muncul dalam:

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- respons carian
- `POST /v1/export`
- penghantaran aliran v1.1

### 5.2 Penyembunyian kewujudan

Entri di luar skop MESTI disembunyikan pada permukaan ejen.

- `GET /v1/knowledge/{id}` MESTI mengembalikan `404 Not Found`, bukan `403 Forbidden`,
  untuk id di luar skop
- entri yang ditapis MESTI TIDAK menyumbang kepada jumlah respons

### 5.3 Penolakan tulis

`POST /v1/knowledge` MESTI ditolak dengan `403 Forbidden` jika:

- label berkesan entri berada di luar grant tulis, atau
- kelas sensitiviti berkesan entri melebihi `oamp_sensitivity_max`, atau
- `source.agent_id` bertentangan dengan `oamp_agent_id`

### 5.4 Penolakan import

`POST /v1/import` MESTI menolak entri yang melebihi grant tulis dan MESTI mengira
mereka dalam medan `rejected` respons import.

### 5.5 Penapisan eksport

`POST /v1/export` MESTI mengembalikan hanya entri yang boleh dibaca di bawah grant, kecuali
`oamp_export_full` ada dan dibenarkan di bawah pengesahan pengguna langsung.

### 5.6 Penapisan aliran

Jika backend menyokong penstriman v1.1, ia MESTI:

- mengabaikan `knowledge_created` dan `knowledge_updated` untuk entri di luar skop
- mengabaikan `knowledge_deleted` untuk entri yang tidak dibenarkan untuk dibaca oleh ejen

---

## 6. Penambahan Kemampuan

v1.3 memperluas blok kemampuan tadbir urus v1.2:

```json
{
  "oamp_version": "1.3.1",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false,
      "enforcement": {
        "supported": true,
        "spec_version": "1.3.1",
        "label_hierarchy": "dotted-prefix",
        "reserved_top_level_labels": [
          "identity", "location", "health", "finance",
          "relationships", "work", "preferences",
          "creative", "beliefs", "behaviour"
        ],
        "grant_transport": ["jwt-claims", "oamp-grant-header"],
        "existence_hiding": true,
        "stream_filtering": true,
        "export_full_supported": true,
        "mediation": {
          "supported": true,
          "trusted_issuers": ["governor"]
        },
        "provenance_query": ["task_id", "context_id"]
      }
    }
  }
}
```

| Medan | Jenis | Keperluan | Penerangan |
|-------|-------|-----------|------------|
| `enforcement.supported` | boolean | MUST jika `enforcement` ada | Backend menerapkan peraturan penguatkuasaan v1.3 |
| `enforcement.spec_version` | string | MUST | Garis spesifikasi v1.3 yang dilaksanakan |
| `enforcement.label_hierarchy` | string | MUST | `dotted-prefix` untuk draf ini |
| `enforcement.reserved_top_level_labels` | array of string | MUST | Label tahap atas yang terpelihara untuk interoperabiliti |
| `enforcement.grant_transport` | array of string | MUST | Mekanisme pengangkutan grant yang disokong |
| `enforcement.existence_hiding` | boolean | MUST | Sama ada id di luar skop disembunyikan sebagai 404 |
| `enforcement.stream_filtering` | boolean | MUST | Sama ada aliran v1.1 ditapis |
| `enforcement.export_full_supported` | boolean | MUST | Sama ada tuntutan eksport penuh dihormati |
| `enforcement.mediation` | object | MAY | Sokongan mediasi dan pengenalan penerbit yang dipercayai |
| `enforcement.provenance_query` | array of string | MAY | Penapis konteks provenance yang disokong (`task_id`, `context_id`) |

---

## 7. Penambahan Log Audit

Kosa kata tindakan audit mendapat:

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read` MESTI TIDAK mencatat kandungan entri yang dilindungi dan SHOULD mengelakkan
mencatat id entri yang ditapis pada permukaan ejen.

---

## 8. Peraturan Keserasian

### 8.1 Backend v1.3

- MESTI terus menerima dokumen v1.0, v1.1, dan v1.2
- MESTI memelihara `governance` dan `provenance` v1.2
- MESTI mengiklankan sokongan penguatkuasaan dengan tepat

### 8.2 Klien v1.0-v1.2

- BOLEH mengabaikan blok `governance.enforcement` jika mereka tidak memahaminya
- MESTI TIDAK menyimpulkan semantik hasil yang ditahan yang boleh dibawa dari string versi `1.3.0` sahaja

### 8.3 Token tanpa grant

Pada backend yang menguatkuasakan v1.3 untuk permukaan ejen, token yang tidak
menyediakan `oamp_read_labels` yang boleh digunakan MESTI dianggap sebagai baca-tiada.

Penyebaran BOLEH masih menyediakan laluan pengesahan pengguna langsung yang berasingan di luar
format grant yang boleh dibawa.

---

## 9. Skema Dan Artifak OpenAPI

Draf v1.3 diwakili oleh:

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

Skema entry dan store kekal additive ke atas v1.2. Novelti utama v1.3 adalah
kontrak kemampuan penguatkuasaan dan tingkah laku backend normatif yang ditakrifkan
dalam draf ini.
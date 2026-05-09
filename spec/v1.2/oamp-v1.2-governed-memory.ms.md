# Protokol Memori Agen Terbuka — Memori yang Dikenakan untuk v1.2

**Status:** Stabil  
**Tarikh:** 2026-05-09  
**Pengarang:** Jonathan Conway (Deep Thinking)  
**Pelaksanaan berkaitan:** `cosmictron`, `kizuna-mem`, `ultra`, `toraeru`  
**Bergantung kepada:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`

---

## 1. Mengapa ini wujud

Pelbagai backend OAMP kini memerlukan memori yang dikenakan kelas pertama:

- **kizuna-mem** memerlukan kelas sensitiviti tahap perusahaan, penilaian polisi yang menyedari asal usul, dan alasan penahanan yang terstruktur.
- **cosmictron** memerlukan pengendalian yang boleh berinteroperasi untuk memori yang terikat kepada polisi dan metadata tadbir urus yang dieksport/dipindahkan.
- **ultra** akan menggunakan dan menghasilkan memori yang dikenakan, jadi blob `metadata.*` yang khusus kepada vendor tidak lagi mencukupi jika kita ingin kebolehan pemindahan backend.
- **toraeru** akan berintegrasi dengan OAMP dan memerlukan kontrak metadata yang sama yang boleh dipindahkan dan bukannya muatan tadbir urus yang khusus kepada backend.

Hari ini, OAMP v1.0/v1.1 hanya boleh membawa data memori yang dikenakan sebagai sambungan vendor di dalam `metadata`, dan itu adalah mematuhi. Namun:

1. tiada bentuk standard untuk metadata tadbir urus,
2. tiada pengiklanan keupayaan standard untuk memori yang dikenakan,
3. tiada representasi yang boleh dipindahkan untuk asal usul pelbagai sumber yang lebih kaya,
4. tiada konsep standard tahap wayar tentang “ditahan” atau “stub yang disunting”.

Cadangan ini menstandardkan tiga yang pertama sebagai **kerja tambahan v1.2** dan secara jelas menangguhkan yang keempat kepada **v2.0**, kerana skema v1.x semasa dan peraturan muatan streaming tidak membenarkan stub yang disunting yang boleh dipindahkan tanpa perubahan yang merosakkan.

---

## 2. Ringkasan Cadangan

### Menstandardkan dalam v1.2

- Objek `governance` yang pilihan pada `KnowledgeEntry`
- Objek sambungan `provenance` yang pilihan pada `KnowledgeEntry`
- Pengiklanan `GET /v1/capabilities` untuk sokongan tadbir urus
- Kunci penapis yang menyedari tadbir urus yang pilihan untuk carian/streaming
- Ujian pematuhan untuk medan memori yang dikenakan dan toleransi pusingan

### Tangguh kepada v2.0

- Dokumen hasil yang disunting/ditahan yang distandardkan
- Bentuk respons REST yang distandardkan yang boleh menggabungkan entri yang boleh dilihat dan stub yang ditahan
- Jenis acara streaming yang distandardkan untuk pengetahuan yang ditahan

---

## 3. Mengapa stub yang ditahan bukan perubahan v1.2

Cadangan ini secara sengaja **tidak** menstandardkan stub yang ditahan dalam v1.2.

Sebab-sebab:

1. Dalam v1.0, `KnowledgeEntry.content` adalah diperlukan dan MUST menjadi string yang tidak kosong.
2. Respons carian/senarai ditakrifkan berdasarkan array objek `KnowledgeEntry`.
3. Streaming v1.1 menyatakan `knowledge_created` dan `knowledge_updated` membawa penuh `KnowledgeEntry`.

Ini bermakna “stub” yang boleh dipindahkan seperti:

```json
{
  "type": "knowledge_entry",
  "content": null,
  "withheld": true
}
```

tidak sah dalam istilah skema v1.x semasa. Membuat `content` pilihan atau boleh null akan menjadi perubahan skema yang merosakkan, bukan tambahan.

Jadi pembahagian standard yang betul adalah:

- **v1.2:** menstandardkan metadata tadbir urus dan penemuan
- **v2.0:** menstandardkan semantik hasil yang ditahan

Backend MAY terus melaksanakan tingkah laku penahanan khusus vendor dalam sambungan mereka sendiri sehingga reka bentuk v2.0 dilaksanakan.

---

## 4. Tambahan Cadangan v1.2

## 4.1 Medan `governance` yang pilihan pada `KnowledgeEntry`

Tambah medan baru yang pilihan di peringkat atas:

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

### Bentuk medan yang dicadangkan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `governance` | objek | MAY | Metadata memori yang dikenakan yang standard |
| `governance.sensitivity_class` | string | MUST jika `governance` ada | Salah satu daripada `public`, `internal`, `confidential`, `restricted` |
| `governance.labels` | array string | MAY | Label tadbir urus yang ditakrifkan oleh backend atau penyewa |
| `governance.handling` | objek | MAY | Petunjuk tadbir urus khusus permukaan |
| `governance.handling.retrieval` | string | MAY | `governed` atau `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` atau `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` atau `ungoverned` |

### Nota

- Medan ini adalah **deskriptif**, bukan bahasa polisi penuh.
- Ia memberitahu backend dan agen lain bagaimana pengetahuan itu diklasifikasikan.
- Ia **tidak** menstandardkan peraturan penilaian kawalan akses.
- Backend MAY memetakan struktur polisi tempatan yang lebih kaya ke dalam `metadata` di samping medan `governance` yang standard.

## 4.2 Medan `provenance` yang diperluas yang pilihan pada `KnowledgeEntry`

Kekalkan `source` tepat seperti sedia ada dan tambah struktur asal usul yang lebih kaya yang pilihan:

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

### Bentuk medan yang dicadangkan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `provenance` | objek | MAY | Metadata keturunan yang diperluas |
| `provenance.sources` | array | MUST jika `provenance` ada | Senarai bukti/sumber yang teratur |
| `provenance.sources[].session_id` | string | MUST | Pengenal sesi sumber |
| `provenance.sources[].timestamp` | string | MUST | Masa pemerolehan ISO 8601 |
| `provenance.sources[].agent_id` | string | MAY | Pengenal agen sumber |
| `provenance.sources[].turn_id` | string | MAY | Pengenal tempatan pusingan/mesej |
| `provenance.derived` | boolean | MAY | Sama ada entri ini disintesis dari pelbagai sumber |

### Nota

- `source` kekal wajib dan kekal sebagai kontrak asal usul minimum.
- `provenance` adalah sambungan keturunan yang lebih kaya dan boleh berinteroperasi untuk backend yang menyokong penggabungan, sintesis, atau rantaian bukti.

## 4.3 Pengiklanan keupayaan tadbir urus

Tambah objek `governance` yang pilihan di bawah `/v1/capabilities.capabilities`:

```json
{
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

### Medan yang dicadangkan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `governance.supported` | boolean | MUST jika `governance` ada | Backend memahami medan tadbir urus yang distandardkan |
| `governance.sensitivity_classes` | array string | MUST | Kelas yang diterima oleh backend |
| `governance.labels_supported` | boolean | MUST | Sama ada label tadbir urus bentuk bebas disimpan/dipelihara |
| `governance.extended_provenance_supported` | boolean | MUST | Sama ada `provenance` disimpan/dipelihara |
| `governance.withheld_stub_support` | boolean | MUST | Sama ada backend mempunyai sebarang tingkah laku stub yang ditahan yang tidak standard |

`withheld_stub_support` adalah maklumat dalam v1.2 sahaja. Ia tidak menunjukkan format wayar yang distandardkan.

## 4.4 Penapis yang menyedari tadbir urus yang pilihan

Di mana backend menyokong pengiklanan penapis, standardkan kunci pilihan ini:

| Kunci | Jenis | Semantik |
|-------|------|-----------|
| `sensitivity_class` | array string | Padankan entri yang `governance.sensitivity_class` ada dalam set |
| `governance_label` | array string | Padankan entri yang mengandungi sekurang-kurangnya satu label tadbir urus yang disenaraikan |

Ini terpakai kepada:

- Carian REST, di mana disokong oleh model pertanyaan khusus backend
- `streaming.filter_keys`, apabila streaming disokong

Kunci ini adalah pilihan kerana tidak setiap backend mengindeks metadata tadbir urus.

---

## 5. Impak Skema Dan OpenAPI

Cadangan ini memerlukan skema versi kecil baru kerana skema JSON v1.0 semasa menetapkan `additionalProperties: false` pada item `KnowledgeEntry` dan `KnowledgeStore`.

Jadi kerja v1.2 mesti merangkumi:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

dengan medan pilihan tambahan:

- `governance`
- `provenance`

Tiada medan yang diperlukan berubah dalam v1.2.

---

## 6. Peraturan Keserasian

### Tingkah laku backend v1.2

- MUST menerima dokumen v1.0 dan v1.1.
- MUST memelihara `governance` dan `provenance` apabila disediakan, kecuali polisi atau sekatan penyimpanan yang didokumenkan secara jelas menolak mereka.
- MUST mengabaikan metadata vendor tambahan yang tidak dikenali seperti sebelum ini.

### Tingkah laku klien v1.0 / v1.1

- Klien v1.0 atau v1.1 boleh mengabaikan `governance` dan `provenance` jika ia tidak memahaminya.
- Ini selamat kerana kedua-duanya adalah medan pilihan tambahan.

### Jangkaan import/export

- Backend yang menyokong tadbir urus SHOULD memelihara medan tadbir urus yang distandardkan merentasi eksport/import.
- Backend yang tidak menyokong tadbir urus SHOULD masih menerima dokumen dan sama ada memelihara medan sebagai data legap atau mendokumenkan bahawa mereka dibuang.

---

## 7. Sasaran Tidak Untuk v1.2

Yang berikut secara jelas di luar skop untuk cadangan ini:

- Bahasa polisi benarkan/tolak yang distandardkan
- Semantik pengesahan silang backend
- `withholding_reason` yang distandardkan
- Bentuk stub `KnowledgeEntry` yang disunting yang distandardkan
- Semantik langganan pelbagai pengguna

Itu memerlukan sama ada:

- reka bentuk v2.0 yang berasingan, atau
- sampul respons/acara baru yang bukan `KnowledgeEntry` yang tidak sesuai dengan jangkaan v1.x semasa.

---

## 8. Tambahan Pematuhan

Jika v1.2 dilaksanakan, tambah kes pematuhan untuk:

- `POST /v1/knowledge` menerima `governance`
- `POST /v1/knowledge` menerima `provenance`
- `GET /v1/knowledge/:id` pusingan medan tadbir urus yang distandardkan
- `POST /v1/import` memelihara tadbir urus/provenance di mana disokong
- `/v1/capabilities` mengiklan sokongan tadbir urus dengan tepat

Jangan **tambahkan** ujian pematuhan stub yang ditahan dalam v1.2.

---

## 9. Pecahan Isu Cadangan Upstream

### Isu 1: Ratifikasi pembahagian skop memori yang dikenakan

Tentukan dan dokumen:

- v1.2 menstandardkan metadata tadbir urus + penemuan
- v2.0 mengendalikan semantik hasil yang ditahan/disunting

### Isu 2: Tambah `governance` dan `provenance` ke skema v1.2

Fail:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`
- pustaka jenis rujukan

### Isu 3: Pengiklanan keupayaan dan kunci penapis

Fail:

- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.2/openapi.yaml`
- teks keupayaan v1.1 jika digunakan semula atau digantikan

### Isu 4: Liputan suite pematuhan

Fail:

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

### Isu 5: Sokongan backend rujukan

Fail:

- `reference/server/`
- jenis rujukan bahasa

### Isu 6: RFC v2.0 untuk hasil yang ditahan

Buka trek reka bentuk berasingan untuk:

- pilihan sampul yang tidak merosakkan berbanding perubahan skema versi utama
- semantik REST untuk ditahan oleh polisi
- semantik streaming untuk kemas kini yang ditahan
- kebolehan pemindahan `withholding_reason`

---

## 10. Cadangan

Adopt cadangan ini sebagai arah kerja:

1. menstandardkan metadata memori yang dikenakan dalam v1.2,
2. menstandardkan asal usul yang lebih kaya dalam v1.2,
3. meninggalkan semantik penahanan/disunting di luar v1.2,
4. membuka RFC v2.0 berasingan untuk hasil yang ditahan yang boleh dipindahkan.

Itu memberikan `cosmictron`, `kizuna-mem`, `ultra`, dan `toraeru` sasaran berinteroperasi yang sama sekarang, tanpa berpura-pura bahawa bentuk `KnowledgeEntry` v1.x semasa sudah dapat mengekspresikan setiap tingkah laku memori yang dikenakan yang kita inginkan.
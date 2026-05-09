# Protokol Memori Ejen Terbuka — Versi 1.1.0

**Status:** Stabil  
**Tarikh:** 2026-05-09  
**Pengarang:** Jonathan Conway (Deep Thinking)  
**Menggantikan:** Tiada — memperluas v1.0.0 secara tambahan  
**Repositori:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstrak

OAMP v1.1 adalah versi minor **secara ketat tambahan** ke atas v1.0.0. Ia mendefinisikan dua
kemampuan yang OPTIONAL yang ditangguhkan secara sengaja oleh v1.0 kepada "pertimbangan masa depan":

- **pengangkutan langganan streaming** yang membolehkan klien menerima
  acara `KnowledgeEntry` dan `UserModel` secara masa nyata melalui WebSocket.
- **parameter kueri `as_of` bitemporal** untuk titik akhir bacaan, membolehkan klien
  untuk menyoal keadaan memori seperti yang wujud pada masa lalu.

Backend yang mematuhi v1.1 MUST masih memenuhi setiap keperluan v1.0. Kedua-dua
kemampuan baru diiklankan melalui **titik akhir penemuan kemampuan** kecil
supaya klien v1.0 tetap interoperable. v1.1 tidak memperkenalkan sebarang perubahan skema atau
titik akhir yang merosakkan, dan klien v1.0 tetap serasi dengan backend v1.1.

Motivasi untuk mempromosikan ini dari "skop v2.0" kepada v1.1 OPTIONAL adalah
praktikal: pelaksanaan rujukan (cosmictron, kizuna-mem) memerlukan kedua-dua
kemampuan untuk menyampaikan permukaan produk yang berguna, dan ketiadaan bahkan
spesifikasi OPTIONAL untuk mereka mencipta sambungan vendor yang tidak serasi sebelum
ekosistem mempunyai peluang untuk selaras.

Kata kunci "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", dan "OPTIONAL" dalam dokumen ini harus
ditafsirkan seperti yang diterangkan dalam [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Hubungan dengan v1.0

v1.1 menggunakan semula **semua** skema, titik akhir, keperluan, dan semantik v1.0
tanpa pengubahsuaian. Hanya penambahan dalam §3 dan §4 yang baru. Dokumen
SHOULD menetapkan `oamp_version` kepada `"1.1.0"` hanya apabila mereka menggunakan
bidang khusus v1.1; jika tidak, `"1.0.0"` tetap betul dan lebih disukai untuk kebolehpindahan.

Backend v1.1 MUST menerima dokumen dengan `oamp_version` sama ada `"1.0.0"`
atau `"1.1.0"`. Backend v1.0 MUST menolak dokumen `"1.1.0"` yang mengandungi
bidang khusus v1.1 yang tidak difahami (mengikut v1.0 §10.2 — peraturan
keserasian versi utama); walau bagaimanapun, memandangkan v1.1 tidak memperkenalkan
sebarang bidang keperluan baru di peringkat atas, backend v1.0 SHOULD menerima
dokumen `"1.1.0"` yang hanya mengandungi bidang v1.0, mengabaikan label versi.

---

## 2. Penemuan Kemampuan

v1.1 memperkenalkan satu titik akhir baru yang membolehkan klien menemui kemampuan
OPTIONAL yang disokong oleh backend.

### 2.1 GET `/v1/capabilities`

Mengembalikan objek JSON yang menerangkan permukaan protokol backend.

**Respons:**

```json
{
  "oamp_version": "1.1.0",
  "capabilities": {
    "streaming": {
      "supported": true,
      "subprotocol": "oamp.v1",
      "endpoint": "/v1/stream",
      "event_types": ["knowledge_created", "knowledge_updated",
                      "knowledge_deleted", "user_model_updated"]
    },
    "as_of": {
      "supported": true,
      "endpoints": ["/v1/knowledge", "/v1/knowledge/{id}",
                    "/v1/user-model/{user_id}"],
      "min_resolution_ms": 1
    },
    "user_id_format": {
      "description": "tenant:node composite (contoh: '1:user')",
      "pattern": "^[0-9]+:.+$"
    },
    "id_preservation": "preserved",
    "content_types": ["application/json", "application/protobuf"],
    "auth_schemes": ["bearer"]
  }
}
```

**Keperluan:**

- Backend yang mengiklankan v1.1 MUST melaksanakan titik akhir ini.
- Semua `capabilities.*.supported` bidang MUST adalah boolean.
- Klien SHOULD memanggil titik akhir ini paling banyak sekali setiap jangka hayat sambungan dan
  menyimpan hasilnya.
- Backend MAY menyertakan kunci khusus vendor di bawah
  `capabilities.metadata` (objek). Klien MUST bertoleransi terhadap kunci yang tidak dikenali.

**`user_id_format` (REQUIRED):**

Backend MUST mengiklankan format pengkodan `user_id` mereka supaya klien
yang menghubungkan beberapa backend OAMP dapat memeriksa keserasian sebelum
mencuba import/export silang backend. Objek ini mengandungi:

| Bidang | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `description` | string | MUST | Penerangan yang boleh dibaca manusia tentang format (contoh: `"tenant:node composite (contoh: '1:user')"`, `"64-char lowercase hex Ed25519 public key"`). |
| `pattern` | string | MAY | Regex ECMA-262 yang sepadan dengan nilai `user_id` yang sah untuk backend ini. Klien MAY menggunakan ini untuk pra-validasi. |

Bidang `user_id` dalam dokumen OAMP kekal sebagai string opak (tiada sekatan format dalam skema). Iklan kemampuan adalah untuk pemeriksaan keserasian di sisi klien sahaja. Klien yang menghubungkan backend dengan format `user_id` yang tidak serasi MUST mengubah nilai `user_id` semasa pemindahan silang backend (ini adalah tanggungjawab klien, bukan tanggungjawab backend).

**`id_preservation` (REQUIRED):**

Sebuah string yang menunjukkan sama ada backend mengekalkan ID entri yang diberikan oleh klien
semasa `POST /v1/import`. Salah satu daripada:

- `"preserved"` -- Backend menyimpan dan mengembalikan `id` yang diberikan oleh klien
  tanpa perubahan. Bidang `id_mappings` dalam respons import akan sentiasa kosong `{}`.
- `"regenerated"` -- Backend MAY memberikan ID baru kepada entri yang diimport
  (contoh: derivasi deterministik dari kunci dalaman). Bidang `id_mappings`
  dalam respons import MUST mengandungi pemetaan dari setiap ID asal
  kepada ID baru yang diberikan.

Klien yang menghubungkan beberapa backend OAMP dan menggunakan ID entri sebagai kunci penyertaan
MUST memeriksa `id_preservation` dan, jika `"regenerated"`, menerapkan `id_mappings`
dari respons import untuk mengekalkan integriti rujukan.

### 2.2 Keserasian Terbalik v1.0

Backend v1.0 akan mengembalikan `404 Not Found` untuk `/v1/capabilities`. Klien
MUST menganggap respons ini sebagai "backend adalah v1.0; tiada kemampuan OPTIONAL
yang tersedia" dan kembali kepada tingkah laku hanya REST. Backend v1.0 juga tidak
mengiklankan `user_id_format` atau `id_preservation`; klien yang menghubungkan beberapa
backend MUST mengendalikan ini dengan baik (lihat §5).

### 2.3 Bentuk Respons Import (Penjelasan v1.0 §6.4)

v1.0 §6.4 mendefinisikan `POST /v1/import` sebagai mengembalikan "`200 OK` dengan ringkasan"
tetapi tidak menetapkan kod status atau bentuk badan respons. v1.1 mewajibkan yang berikut:

**Kod status:** `201 Created`. (Klien MUST juga menerima `200 OK` dari
backend v1.0 untuk keserasian terbalik.)

**Badan respons:**

```json
{
  "imported": 5,
  "skipped": 0,
  "rejected": 0,
  "id_mappings": {
    "88f88510-928b-49d9-aff1-4f32acbf1f97": "a299eeae-39ac-4248-ae24-007302cb64fc"
  }
}
```

| Bidang | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `imported` | integer | MUST | Bilangan entri yang berjaya diimport. |
| `skipped` | integer | MUST | Bilangan entri yang dilepaskan (contoh: duplikat dengan keyakinan yang sama atau lebih tinggi). |
| `rejected` | integer | MUST | Bilangan entri yang ditolak kerana ralat pengesahan. |
| `id_mappings` | object | MUST | Pemetaan ID asal kepada ID yang diberikan. Kosong `{}` jika semua ID dipelihara. Lihat §2.4. |
| `rejections` | array | MAY | Butiran tentang entri yang ditolak. Setiap elemen: `{"id": "...", "reason": "..."}`. |

### 2.4 Pemeliharaan ID Entri semasa Import (Penjelasan v1.0 §4.4)

Pelaksanaan MAY mengekalkan atau menghasilkan semula ID entri semasa import, tetapi
MUST menyampaikan hasilnya melalui respons import:

- **Backend yang mengekalkan ID** (diiklankan sebagai `id_preservation: "preserved"` dalam
  kemampuan): menyimpan `id` yang diberikan oleh klien tanpa perubahan. Bidang `id_mappings`
  dalam respons import MUST adalah `{}`.
- **Backend yang menghasilkan semula ID** (diiklankan sebagai `id_preservation: "regenerated"`
  dalam kemampuan): memberikan ID baru semasa import (contoh: melalui derivasi deterministik).
  Bidang `id_mappings` dalam respons import MUST memetakan setiap ID asal entri yang diimport kepada
  ID baru yang diberikan.

Ini mengakomodasi kedua-dua pola seni bina tanpa memerlukan mana-mana untuk
mengubah reka bentuk dalaman mereka. Klien yang bergantung kepada kestabilan ID (contoh: ejen
yang membina graf memori yang dikunci pada ID entri) MUST memeriksa `id_mappings` dan
mengemas kini rujukan mereka selepas import.

---

## 3. Pengangkutan Streaming (OPTIONAL)

### 3.1 Motivasi

OAMP v1.0 adalah berdasarkan polling: klien mengetahui tentang perubahan memori dengan mengeluarkan
kueri pencarian semula. Untuk ejen interaktif, permukaan kebolehan pengamatan, dan papan pemuka
ini mencipta sama ada beban polling yang tinggi atau UI yang tidak terkini. v1.1 mendefinisikan subprotokol WebSocket
yang membolehkan klien melanggan mutasi memori semasa ia berlaku.

Ini adalah OPTIONAL kerana (a) tidak setiap backend mempunyai sumber acara masa nyata,
dan (b) model polling dalam v1.0 tetap betul dan mencukupi untuk ejen batch.

### 3.2 Titik Akhir

Backend v1.1 dengan sokongan streaming MUST mendedahkan:

- **URL:** `wss://{host}/v1/stream` (atau `ws://` untuk pembangunan bukan TLS)
- **Subprotokol:** `oamp.v1` (dirundingkan melalui header `Sec-WebSocket-Protocol` WebSocket standard)

Jika klien tidak meminta `oamp.v1` dalam senarai subprotokol, backend MUST menolak
peningkatan dengan HTTP `400 Bad Request`.

### 3.3 Pengesahan

Peningkatan WebSocket MUST mengesahkan cara yang sama seperti API REST. Backend
SHOULD menerima token pembawa melalui header `Authorization` pada permintaan peningkatan, dan
MAY menerimanya sebagai parameter kueri `?token=` untuk klien pelayar yang tidak dapat menetapkan header
pada peningkatan WebSocket. Skema yang dipilih MUST dinyatakan dalam `/v1/capabilities`.

### 3.4 Format Frame

Semua frame adalah **frame teks** yang membawa satu objek JSON. (Frame binari
dikhaskan untuk streaming mod protobuf masa depan dan MUST NOT digunakan dalam v1.1.)

Setiap frame mempunyai bentuk:

```json
{
  "oamp_version": "1.1.0",
  "type": "<frame_type>",
  "id": "<uuid_v4>",
  "ts": "<iso8601>",
  "payload": { ... }
}
```

`id` adalah pengenal per-frame yang digunakan klien untuk mengaitkan balasan; `ts`
adalah cap waktu monotonic backend pada saat frame dikeluarkan.

### 3.5 Frame Klien → Server

| `type`         | Tujuan                                            |
|----------------|----------------------------------------------------|
| `subscribe`    | Membuka langganan dengan penapis.                  |
| `unsubscribe`  | Menutup langganan yang telah dibuka sebelum ini.   |
| `ping`         | Ujian kehadiran; backend MUST menjawab dengan `pong`.  |

**`subscribe` payload:**

```json
{
  "subscription_id": "<string-yang-dipilih-klien>",
  "user_id": "user-123",
  "event_types": ["knowledge_created", "knowledge_updated"],
  "filters": {
    "category": ["preference", "correction"],
    "tags": ["language"]
  },
  "include_initial_snapshot": false
}
```

- `subscription_id` adalah pilihan klien dan MUST unik bagi setiap sambungan. Pelayan menggunakannya pada setiap acara seterusnya dan pada pengesahan unsubscribe.
- `user_id` adalah REQUIRED. Backend MUST menolak langganan silang pengguna
  (mengembalikan frame `error` dengan kod `"forbidden"`).
- `event_types` MAY diabaikan untuk melanggan semua jenis acara yang disokong oleh backend.
- `filters` adalah OPTIONAL; kunci penapis yang diiktiraf disenaraikan dalam §3.7. Kunci penapis yang tidak dikenali MUST diabaikan, tidak ditolak.
- `include_initial_snapshot` (default `false`): jika `true`, backend MUST
  mengeluarkan satu frame `knowledge_snapshot` yang mengandungi keadaan yang sepadan sebelum sebarang acara langsung mengalir.

### 3.6 Frame Server → Klien

| `type`                | Tujuan                                              |
|-----------------------|------------------------------------------------------|
| `subscribed`          | Mengakui langganan.                                |
| `unsubscribed`        | Mengakui pengesahan langganan.                     |
| `knowledge_created`   | Sebuah `KnowledgeEntry` baru telah disimpan.       |
| `knowledge_updated`   | Sebuah `KnowledgeEntry` yang sedia ada telah diubah (PATCH). |
| `knowledge_deleted`   | Sebuah `KnowledgeEntry` telah dipadam secara kekal. |
| `knowledge_snapshot`  | Snapshot satu kali untuk `include_initial_snapshot`. |
| `user_model_updated`  | Baris `UserModel` telah dikemas kini.               |
| `error`               | Ralat protokol atau aplikasi.                       |
| `pong`                | Balasan kehadiran.                                  |

**`knowledge_created` payload:**

```json
{
  "subscription_id": "<echoed-from-subscribe>",
  "entry": { /* dokumen KnowledgeEntry v1.0 penuh */ }
}
```

`knowledge_updated` membawa entri **selepas kemas kini**. `knowledge_deleted`
hanya membawa `{ "subscription_id": "...", "id": "<uuid>", "user_id": "..." }`
untuk memenuhi peraturan v1.0 "tiada kandungan dalam log" walaupun di atas wayar — kandungan yang dipadam MUST NOT disiarkan semula.

**`error` payload:**

```json
{
  "subscription_id": "<id-atau-null>",
  "code": "forbidden | invalid | rate_limited | internal",
  "message": "boleh dibaca manusia",
  "retryable": false
}
```

### 3.7 Kunci Penapis yang Dikenali

| Kunci       | Jenis            | Semantik                                  |
|-------------|-----------------|--------------------------------------------|
| `category`  | array of string  | Padankan mana-mana kategori v1.0 ini.     |
| `tags`      | array of string  | Entri MUST mengandungi sekurang-kurangnya satu tag yang disenaraikan. |
| `min_confidence` | number      | `confidence` entri MUST ≥ nilai ini.     |

Backend MAY menyokong kunci penapis tambahan; mereka MUST diiklankan dalam
`/v1/capabilities.streaming.filter_keys`.

### 3.8 Tekanan Balik & Penghantaran

- Protokol adalah **paling sekali**. Jika klien tidak dapat mengikuti, backend
  MAY menjatuhkan acara dan SHOULD mengeluarkan satu frame `error` dengan kod
  `"rate_limited"` dan `retryable: true` untuk menandakan jurang. Klien yang memerlukan
  semantik tepat sekali MUST menyelaraskan melalui polling `/v1/knowledge`.
- Backend MUST menutup WebSocket selepas 60 saat tanpa trafik klien
  (tiada `ping`, tiada frame lain). Klien SHOULD menghantar `ping` setiap 30 saat.
- Backend MUST bertoleransi sekurang-kurangnya 16 langganan serentak bagi setiap sambungan.

### 3.9 Privasi

Peraturan privasi v1.0 §8 terpakai kepada kandungan yang disiarkan seolah-olah ia adalah respons REST:

- Kandungan pengetahuan MUST NOT dicatat di mana-mana sisi sambungan.
- Frame `knowledge_deleted` MUST NOT termasuk kandungan yang dipadam.
- Langganan MUST dibatasi kepada satu `user_id`. Penggandaan multi-pengguna adalah kebimbangan v2.0.

---

## 4. Parameter Kueri `as_of` Bitemporal (OPTIONAL)

### 4.1 Motivasi

Banyak backend memori (cosmictron, kizuna-mem, yang lain) sudah menyimpan
data bitemporal — paksi `valid_time` (apabila fakta itu benar di dunia)
dan paksi `ingest_time` (apabila sistem mengetahui fakta tersebut). v1.0 tiada
cara untuk bertanya "apa yang anda ketahui pada masa T?", yang diperlukan untuk:

- Ulang main dan penyahpepijatan keputusan ejen.
- Audit pematuhan ("apa yang ada dalam fail apabila keputusan ini dibuat?").
- UI perjalanan masa terbalik dalam papan pemuka kebolehan pengamatan.

v1.1 mendefinisikan satu parameter kueri yang tunggal dan boleh digunakan secara universal yang mendedahkan
kemampuan penyimpanan ini tanpa menentukan representasi dalaman.

### 4.2 Parameter

Backend dengan sokongan `as_of` MUST menerima parameter kueri berikut pada
titik akhir yang disenaraikan di bawah:

```
?as_of=<iso8601-datetime>
```

Titik akhir yang terjejas:

| Titik Akhir                          | Semantik dengan `as_of`                          |
|-----------------------------------|-------------------------------------------------|
| `GET /v1/knowledge?query=...`     | Cari indeks seperti yang wujud pada `as_of`.      |
| `GET /v1/knowledge/{id}`          | Kembalikan keadaan entri pada `as_of`.         |
| `GET /v1/user-model/{user_id}`    | Kembalikan model pengguna pada `as_of`.            |

Titik akhir mutasi (`POST`, `PATCH`, `DELETE`) MUST NOT menerima `as_of`
dan MUST menjawab dengan `400 Bad Request` jika parameter tersebut disertakan.

### 4.3 Semantik

Dua paksi semantik adalah mungkin. Backend MUST memilih **semantik ingest_time**
secara lalai: "tunjukkan kepada saya hasil yang sama yang akan dikembalikan oleh
kueri ini jika dikeluarkan tepat pada `as_of`." Ini adalah satu-satunya tafsiran yang ditakrifkan dengan baik secara universal,
dan adalah apa yang dilaksanakan oleh setiap backend rujukan yang diketahui.

Jika backend menyokong kueri `valid_time` (paksi keadaan dunia), ia MUST
mendedahkan mereka melalui parameter yang dinamakan secara berasingan dan jelas (contoh,
`?valid_at=`). v1.1 memperuntukkan `valid_at` untuk tujuan ini tetapi tidak
menstandardkannya; itu adalah kerja v2.0.

### 4.4 Bentuk Respons

Badan respons MUST sama dengan respons v1.0 yang setara. v1.1
hanya mengubah keadaan sejarah yang diterangkan oleh badan tersebut.

Backend yang menyedari v1.1 SHOULD menyertakan header respons
`OAMP-As-Of: <iso8601>` yang mengulangi cap waktu yang digunakannya. Klien MAY menggunakan
ini untuk mengesan normalisasi cap waktu (contoh, backend membundarkan kepada
resolusi penyimpanannya).

### 4.5 Cap Waktu Di Luar Julat

- `as_of` di masa depan MUST dianggap sebagai `now`. Backend SHOULD
  menetapkan `OAMP-As-Of` kepada cap waktu yang diselesaikan sebenar.
- `as_of` sebelum acara ingest pertama pengguna MUST mengembalikan set hasil kosong
  (HTTP 200), bukan 404.
- `as_of` yang tidak dapat diselesaikan oleh backend kerana tamat tempoh/penghapusan
  snapshot MUST mengembalikan `409 Conflict` dengan `code: "as_of_expired"`.

### 4.6 Iklan Kemampuan

`/v1/capabilities.as_of.min_resolution_ms` MUST melaporkan delta masa terkecil
yang dapat diselesaikan oleh backend (contoh, selang snapshot). Klien SHOULD
NOT menganggap resolusi sub-milisaat.

---

## 5. Pematuhan

Backend yang mendakwa **kesesuaian v1.1** MUST:

1. Memenuhi setiap keperluan mandatori v1.0.
2. Melaksanakan `GET /v1/capabilities` yang mengembalikan bendera kemampuan yang benar.
3. Untuk setiap kemampuan OPTIONAL yang diiklankan (`streaming`, `as_of`):
   melaksanakan permukaan penuh yang diterangkan dalam §3 atau §4 masing-masing.
4. Menolak ciri OPTIONAL yang tidak disokong dengan kod ralat HTTP/WebSocket yang didokumenkan; tidak pernah mengabaikan secara senyap.

Backend MAY mendakwa kesesuaian v1.1 dengan **tiada kemampuan OPTIONAL yang disokong**. Ini berguna: ia menandakan kepada klien bahawa backend
memahami kosa kata v1.1 dan akan menampilkan ciri OPTIONAL masa depan
dalam `/v1/capabilities` daripada sebagai sambungan yang tidak dapat ditemui.

Validator di `/validators/validate.sh` akan memperoleh fixture v1.1 dalam
PR yang berasingan; dokumen v1.1 MUST disahkan terhadap Skema JSON v1.0
yang tidak berubah.

---

## 6. Laluan Migrasi untuk Klien v1.0

Klien v1.0 yang berkomunikasi dengan backend v1.1 terus berfungsi tanpa perubahan.
Klien v1.0 yang ingin memilih ciri v1.1:

1. Mengeluarkan `GET /v1/capabilities` dan memeriksa respons.
2. Jika `streaming.supported`, buka WebSocket dan ikuti §3.
3. Jika `as_of.supported`, tambahkan `?as_of=` kepada permintaan bacaan di mana berguna.

Tiada keperluan untuk meningkatkan `oamp_version` dalam dokumen yang disimpan. Rentetan versi
menerangkan dokumen, bukan sesi — klien v1.1 boleh menyimpan dokumen v1.0 dengan baik.

---

## 7. Soalan Terbuka untuk Penetapan v1.1

Ini sedang dipantau untuk perbincangan komuniti sebelum v1.1 ditandakan stabil:

1. **Pemulihan langganan merentasi sambungan semula.** Haruskah klien dapat
   menghantar `since=<event_id>` pada `subscribe` untuk mengulang acara yang terlepas?
   Ini memerlukan backend untuk menyimpan log acara; banyak yang tidak. *Jawapan sementara:*
   serahkan kepada v2.0.
2. **Paginasi snapshot.** Frame `knowledge_snapshot` untuk pengguna dengan
   100k entri adalah satu frame hari ini. Haruskah kita mewajibkan pengchunkan?
   *Jawapan sementara:* mewajibkan `snapshot_chunk` jika backend melaporkan
   had `streaming.snapshot_max_entries`; jika tidak, satu frame.
3. **Standardisasi `valid_at`.** Permintaan sebenar dari kewangan dan pematuhan
   menunjukkan `valid_at` lebih berguna daripada `as_of` untuk beberapa aliran kerja.
   *Jawapan sementara:* letakkan `as_of` dalam v1.1, simpan `valid_at` untuk v1.2 atau
   v2.0 setelah ≥2 backend menghantar pelaksanaan yang saling beroperasi.
4. **Streaming gRPC.** Haruskah subprotokol streaming mempunyai pengikatan gRPC?
   *Jawapan sementara:* direktori `/proto/` akan memperoleh
   `service Stream { rpc Subscribe(stream SubscribeRequest) returns
   (stream Event); }` setelah bentuk JSON stabil.

---

## Lampiran A: Skema Kemampuan

Skema JSON untuk respons `/v1/capabilities` akan ditambahkan di
`spec/v1.1/capabilities.schema.json` setelah §2 dimuktamadkan. Bentuk dalam §2.1
adalah definisi kerja.

## Lampiran B: Sasaran Pelaksanaan Rujukan

Dua backend rujukan akan melaksanakan kemampuan OPTIONAL v1.1 secara serentak
dengan draf ini:

- **cosmictron** (Rust) — `/v1/capabilities`, `/v1/oamp/*` REST,
  `/v1/oamp/stream` subprotokol WebSocket, `?as_of=` pada bacaan memori. Lihat
  `cosmictron/docs/design/OAMP_TRANSPORT.md`.
- **kizuna-mem** (Zig core + Rust sidecar) — permukaan yang sama; WebSocket
  disajikan dari sidecar Rust. Lihat
  `kizuna-dream/docs/design/OAMP_TRANSPORT.md` dan
  `kizuna-dream/docs/design/WEBSOCKET_EVENT_STREAM.md`.

Pelaksanaan ini adalah ujian tekanan kesesuaian untuk spesifikasi; jika
mana-mana tidak dapat melaksanakan dengan baik terhadap draf ini, draf akan disemak
sebelum v1.1 dimuktamadkan.
# Panduan rilis untuk maintainer

Rilis ditangani oleh [Release workflow](../.github/workflows/release.yml).

### Jalur otomatis

1. Update `VERSION` di `SendToCom.py` dan tambahkan catatan di `CHANGELOG.md`.
2. Push ke `main`, lalu pastikan workflow **CI** lulus semua job.
3. Jika CI lulus pada commit terbaru `main`, workflow Release akan membuat tag `vX.Y.Z` **bila belum ada** dan menerbitkan Release dengan source ZIP + `SHA256SUMS.txt`.
4. Jika release/tag versi itu sudah ada, workflow **tidak menimpa** atau memindahkan tag. Rilis versi baru membutuhkan perubahan `VERSION`.

### Jalur manual

Tag versi bisa dibuat manual setelah tes Windows:

```bash
git switch main
git pull --ff-only
git tag -a v2.2.4 -m "BASKA SEND v2.2.4"
git push origin v2.2.4
```

Push tag menjalankan release workflow, atau gunakan tab Actions → Release → Run workflow dengan tag yang telah tersedia. Sebelum rilis, lakukan uji manual Windows untuk popup, system tray, auto-start, pairing, dan upload; CI otomatis tidak menguji seluruh perilaku interaktif Windows.

### Keamanan dan format

- Jangan masukkan PIN, database, cookie, atau file pribadi ke Git/release.
- Arsip adalah **source ZIP** untuk Python; tidak ada EXE/installer tersertifikasi.
- SHA-256 `SHA256SUMS.txt` dipublikasikan agar berkas hasil unduhan dapat diperiksa.

### Rollback

Stop program dan backup data; gunakan ZIP rilis sebelumnya, ganti hanya source Python, restart, cek `--status`. Jangan menimpa atau melakukan downgrade database tanpa backup yang kompatibel.

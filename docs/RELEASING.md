# Panduan rilis untuk maintainer

1. Pastikan CI hijau dan lakukan tes **manual Windows** untuk popup, system tray, pairing, upload, dan firewall.
2. Audit file dan riwayat Git agar tidak mengandung PIN, token, database, atau data pribadi.
3. Update konstanta `VERSION` di `SendToCom.py` dan `CHANGELOG.md`.
4. Buat tag `vX.Y.Z` di commit yang sudah diuji dan push tag tersebut.
5. Workflow [Release](../.github/workflows/release.yml) memverifikasi kecocokan tag dan `VERSION`, menjalankan tes, menghasilkan ZIP Python dan `SHA256SUMS.txt`, lalu membuat GitHub Release.
6. Workflow juga bisa dijalankan manual untuk **tag yang sudah ada** via Actions → Release → Run workflow. Rilis yang sudah ada tidak akan diduplikasi.

Contoh membuat tag setelah perubahan digabungkan:

```bash
git fetch origin
git switch main
git pull --ff-only
git tag -a v2.2.4 -m "BASKA SEND v2.2.4"
git push origin v2.2.4
```

Jangan gunakan ulang tag untuk isi berbeda. Artefak rilis saat ini **ZIP source**, bukan EXE atau installer tersertifikasi.

### Rollback

Hentikan aplikasi, backup direktori data, ganti source dengan paket versi sebelumnya, jalankan server, dan verifikasi `--status`. Bila format database berbeda, gunakan backup yang kompatibel; jangan menimpa data secara otomatis.

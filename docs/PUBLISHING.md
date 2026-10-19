# Checklist publikasi GitHub

Kode, README, banner, logo, lisensi, CI, templates, kebijakan keamanan dan ZIP Release dapat disiapkan lewat Git. Beberapa properti repository adalah **pengaturan GitHub**, bukan file; hanya admin repo yang dapat mengubahnya lewat UI/API dengan hak administrator.

## About → Edit (ikon pensil)

**Description** (salin):
> BASKA SEND — Lightweight Windows LAN messaging and file-sharing hub with private chat, device pairing, native notifications, and a responsive Python WebApp.

**Topics** (saran):
`python`, `windows`, `lan`, `messaging`, `file-sharing`, `local-network`, `sqlite`, `webapp`, `desktop-notifications`

**Website:** biarkan kosong jika belum ada URL dokumentasi resmi; jangan memakai tautan yang tidak dikelola.

## Visibilitas: private → public

1. Lakukan audit terakhir: cek setiap file dan Git history untuk PIN, token, database, screenshot dan data pengguna.
2. Pastikan [CI](https://github.com/baska-pro/sendtocom/actions/workflows/ci.yml) lulus dan [v2.2.4 Release](https://github.com/baska-pro/sendtocom/releases/tag/v2.2.4) ada.
3. Buka repository → **Settings** → **General** → **Danger Zone** → **Change repository visibility** → **Make public**, lalu konfirmasi sesuai petunjuk GitHub.
4. Setelah menjadi Public, uji tautan README, lisensi, assets, Issues dan Releases dari browser tanpa login.
5. Tambahkan social preview image pada Settings → General → Social preview **jika memiliki PNG/JPG yang ingin digunakan**. SVG `assets/banner.svg` sudah tersedia untuk README tetapi tidak otomatis menjadi social preview di Github.

> Perubahan visibility membuat **semua Git history** dapat dilihat publik. Jangan hanya mengandalkan `.gitignore`, karena file yang pernah di-commit tetap muncul dalam riwayat.

## Setelah publik

- Periksa Issues, private security reporting (jika tersedia), default branch, dan permission workflow.
- Gunakan tag `vX.Y.Z` sesuai `VERSION` untuk tiap rilis.
- Pertahankan proteksi branch, review PR, dan pemeriksaan CI sesuai kebutuhan tim.

# Status dan pengelolaan publikasi GitHub

Repository **[baska-pro/sendtocom](https://github.com/baska-pro/sendtocom)** sudah berstatus **Public**. Pengaturan utama dilakukan lewat GitHub CLI (`gh repo edit` dan `gh api`) pada 19 Oktober 2026.

## Metadata tersimpan

- **Description:** BASKA SEND — Lightweight Windows LAN messaging and file-sharing hub with private chat, device pairing, native notifications, and a responsive Python WebApp.
- **Topics:** `python`, `windows`, `lan`, `messaging`, `file-sharing`, `local-network`, `sqlite`, `webapp`, `desktop-notifications`, `self-hosted`.
- **Website:** [Latest GitHub Release](https://github.com/baska-pro/sendtocom/releases/latest).
- **Default branch:** `main`.
- **License:** MIT.
- **Issues & Discussions:** enabled.
- **GitHub Projects & Wiki:** disabled (dokumentasi utama hidup di repo).
- **Delete branches after merging:** enabled.

## Pemeriksaan keamanan GitHub

- **Dependabot security updates:** enabled.
- **Secret scanning:** enabled.
- **Push protection:** enabled.
- **Source audit:** pencarian pola umum token/API keys/webhook/private key/IP hard-coded di source awal tidak menemukan kandidat. Ini bukan jaminan seluruh bug keamanan sudah terselesaikan.
- **Jaringan:** aplikasi tetap menggunakan HTTP tanpa TLS pada LAN, sehingga **jangan** membuka port TCP 8765 ke internet.

Periksa ulang Security tab GitHub secara berkala dan tangani alert valid. Jangan upload file pengguna, PIN, database, atau log ke repository.

## Branding

- Banner README: [assets/banner.svg](../assets/banner.svg).
- Logo vektor: [assets/logo.svg](../assets/logo.svg).
- Kartu media sosial **PNG 1280 × 640**: [assets/social-preview.png](../assets/social-preview.png).

### Satu pengaturan web yang perlu dilakukan secara khusus

GitHub **belum menyediakan endpoint REST/GraphQL publik untuk mengubah Social preview**, jadi `gh repo edit` tidak dapat memasangnya. File PNG sudah siap; untuk menjadikannya preview ketika tautan repository dibagikan:

1. Buka [Repository Settings](https://github.com/baska-pro/sendtocom/settings).
2. Pada bagian **Social preview**, pilih **Edit → Upload an image**.
3. Unggah `assets/social-preview.png` (kurang dari 1 MB).

Meng-commit PNG ke repository **tidak** otomatis menjadikannya Social preview GitHub.

## Release dan CI

- [GitHub Actions CI](https://github.com/baska-pro/sendtocom/actions/workflows/ci.yml) berjalan pada Windows dan Linux untuk Python 3.10/3.12.
- [Release v2.2.4](https://github.com/baska-pro/sendtocom/releases/tag/v2.2.4) memuat source ZIP, checksum SHA-256 dan release notes.
- Release baru hanya dibuat dari versi/tag yang sesuai dengan nilai `VERSION` skrip, setelah pemeriksaan berhasil.

## Hal yang masih membutuhkan pengujian manusia

Lakukan tes Windows nyata untuk popup, balasan pesan, pairing, firewall, auto-start, unggah file dan pembaruan database. Lulus CI smoke test tidak berarti semua skenario interaktif teruji. Sebelum setiap versi baru, audit kembali riwayat Git dan semua artefak rilis.

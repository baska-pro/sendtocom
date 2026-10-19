# Troubleshooting

## HP tidak bisa membuka WebApp

- Jalankan `python SendToCom.py --status` dan periksa IP LAN yang aktif.
- Pastikan HP dan PC pada jaringan yang sama, bukan guest Wi-Fi atau AP dengan client isolation.
- Periksa Windows Firewall profil **Private**; jangan membuka port ke internet.
- Port default `8765` mungkin sudah dipakai aplikasi lain.

## Port sedang digunakan

Di Windows jalankan `netstat -ano | findstr :8765`; identifikasi proses sebelum menghentikannya. Ubah `port` di `%LOCALAPPDATA%\SendToCom\config.json` hanya saat server berhenti dan pastikan aturan firewall ikut diperbarui.

## Popup native tidak ada

Popup, system tray, suara Windows dan dialog native memerlukan Windows serta sesi pengguna yang login. Periksa mode notifikasi pesan dan apakah notifikasi sedang dipause dari tray.

## File ditolak

Ukuran upload default maksimum **50 MB**. Periksa allowlist ekstensi, format internal file, dan larangan executable atau Office macro. Jangan menyamarkan file berbahaya menjadi PDF.

## Auto-start gagal

Cek Windows Task Scheduler task `SendToCom`; path Python dan skrip mesti benar. Jika dipindahkan, jalankan `--install-startup` kembali.

## PIN lupa

Gunakan jalur pengelolaan admin lokal yang tersedia bila masih memiliki akses sah. Jangan membagikan database atau file konfigurasi untuk meminta bantuan.

## Membuat issue

Sertakan versi, OS, Python, langkah reproduksi, dan hasil yang diharapkan. **Samarkan** PIN, token, pesan, alamat internal yang sensitif, dan file pribadi dari log/screenshot.

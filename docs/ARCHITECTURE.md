# Arsitektur

```text
Browser HP / Laptop (trusted LAN)
               |
           HTTP :8765
               |
      ThreadingHTTPServer
        |       |       |
      Auth   Messaging  Files
        |       |       |
    PIN/sesi   SQLite   Folder lokal
                |
           Windows host
       Popup / tray / audio
```

Semua bagian dirangkai dalam **`SendToCom.py`**: server HTTP dan API, WebApp HTML/CSS/JS tertanam, login PIN/pairing/session/CSRF, riwayat SQLite, pengaturan folder, dan popup desktop berbasis Windows.

### Pertimbangan desain
- Tanpa service cloud atau dependensi runtime wajib untuk kemampuan inti.
- Single-file mudah disalin dan dioperasikan tanpa installer.
- Data dan file tersimpan pada PC yang menjalankan program.
- `lan_only` dan firewall hanya bagian dari pembatasan jaringan; **HTTP tidak menyediakan enkripsi transport**.

Perubahan skema database, format session, atau desain keamanan sebaiknya melalui PR terpisah, tes, dan strategi migrasi/rollback.

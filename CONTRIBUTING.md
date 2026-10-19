# Contributing

Terima kasih atas kontribusinya.

1. Cek issue yang sudah ada sebelum membuat laporan atau fitur baru.
2. Buat branch dari `main`, lalu buat Pull Request dengan perubahan yang terfokus.
3. Pertahankan penggunaan Python standard library jika memungkinkan. Tambahkan tes regresi untuk bug.
4. Jalankan `python -m py_compile SendToCom.py`, `python -m unittest discover -s tests -v`, dan `python SendToCom.py --help`.
5. Perubahan notifikasi popup, system tray, Task Scheduler, dan firewall harus diuji **manual pada Windows**.
6. Jelaskan hasil pengujian, risiko, kompatibilitas data SQLite, dan rencana rollback di PR.
7. Perbarui README/CHANGELOG jika mengubah perilaku pengguna.

Jangan menyertakan PIN, data pengguna, konfigurasi lokal atau file pribadi dalam issue/PR. Kirim laporan keamanan melalui [SECURITY.md](SECURITY.md). Hormati [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

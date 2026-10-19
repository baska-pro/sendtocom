# Instalasi BASKA SEND

## Persyaratan

PC server **Windows 10/11**, Python **3.10+**, dan browser modern pada perangkat di jaringan lokal yang sama. Fitur inti memakai Python standard library tanpa `pip install`. Pillow hanya opsional untuk akselerasi tertentu.

## Setup

1. Unduh `SendToCom.py` dari GitHub atau paket source ZIP pada Releases.
2. Simpan pada folder yang **tidak dipindahkan lagi**, contohnya `C:\Tools\SendToCom\`.
3. Buka PowerShell di folder tersebut, lalu jalankan:

```powershell
py -3 SendToCom.py --setup
```

4. Ikuti wizard PIN utama 4–12 digit. Pilih PIN unik, jangan sebarkan.
5. Setup mencoba membuat Task Scheduler auto-start saat login Windows dan membuka Windows Firewall **Private** untuk port aplikasi. Jika firewall gagal, jalankan `py -3 SendToCom.py --firewall-add` dari PowerShell Administrator.

## Menghubungkan HP/laptop

Jalankan `py -3 SendToCom.py --status`, lalu buka LAN URL yang ditampilkan, misalnya `http://192.168.1.10:8765`. HP harus berada pada LAN yang sama, tanpa guest/client isolation. Ikuti login atau pairing melalui WebApp.

**Jangan** menggunakan port forwarding, profil firewall Public, atau router DMZ untuk membuka akses di luar LAN.

## Lokasi data

- Config, database, log: `%LOCALAPPDATA%\SendToCom\`.
- File diterima: `%USERPROFILE%\Downloads\BASKA SEND\` secara default.
- Berkas pin awal saat instalasi, jika masih ada: `FIRST_RUN_PIN.txt` pada direktori data. Simpan secara privat dan ganti PIN awal sesegera mungkin.

## Administrasi

```powershell
py -3 SendToCom.py --status
py -3 SendToCom.py --restart
py -3 SendToCom.py --stop
py -3 SendToCom.py --remove-startup
py -3 SendToCom.py --firewall-remove
```

## Memperbarui versi

1. Hentikan aplikasi, lalu backup direktori data secara aman di luar repo.
2. Ganti **hanya** `SendToCom.py` dengan versi baru.
3. Jalankan `--restart` dan `--status`.
4. Jika path Python/skrip berubah, perbarui auto-start dengan `--install-startup`.

Lihat [Troubleshooting](TROUBLESHOOTING.md) apabila terjadi masalah.

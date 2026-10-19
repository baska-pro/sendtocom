# Security Policy

## Supported version

The latest code on `main` is the primary target for security reports. Backports to older versions are not guaranteed.

## Network security

BASKA SEND is designed for **trusted home/office LAN environments only**. It serves the WebApp over **unencrypted HTTP** by default. PINs, sessions, pairing and CSRF defenses do **not** provide TLS protection against interception of LAN traffic.

**Do not expose port 8765 to the internet, configure WAN port forwarding, disable `lan_only` for public access, or use it on untrusted Wi-Fi.** The Windows Firewall rule should apply only to the **Private** network profile, restricted further where possible.

Use a strong unique PIN, revoke unknown devices, and keep Windows and Python updated. Remote access requires a separately designed encrypted, authenticated transport; direct WAN access is not supported.

## Reporting vulnerabilities

Do **not** file public issues containing exploit instructions, working secrets, message contents, or personal information.

Report privately using [GitHub security advisories](https://github.com/baska-pro/sendtocom/security/advisories/new) if available; otherwise contact the maintainer using the repository owner's public contact details. Include the affected version, minimal reproduction, impact and recommended fix. Do not test unauthorized third-party installations.

## Sensitive data

Never commit `%LOCALAPPDATA%\SendToCom\config.json`, `messages.db`, `FIRST_RUN_PIN.txt`, app logs, session tokens, or users' documents. `.gitignore` protects only untracked paths and does not remove secrets from Git history.

## Known limitations

- No end-to-end encryption or HTTPS on the local service.
- File allowlisting and signature checks are not antivirus or sandboxing.
- User-initiated file-open actions execute on the Windows host.
- PINs supplied as CLI arguments may be recorded by the OS or shell history.

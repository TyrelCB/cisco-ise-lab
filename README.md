# Cisco ISE — DevNet On-Demand Sandbox (Stack Automation)

> **Run this yourself:** free with a Cisco ID. Catalog entry:
> **[developer.cisco.com/sandbox/detail/ise-sandbox](https://developer.cisco.com/sandbox/detail/ise-sandbox)**
> (DevNet Sandboxes, powered by Stack Automation by Quali.)

Reservation **Identity Services Engine (ISE) — 20261105220143** (created 2026-11-05, 4-day runtime).

## Topology

| Node | IP | Role |
|---|---|---|
| ISE Node 1 (ise-node-1) | 10.10.20.77 | Primary PAN (UI + all APIs) |
| ISE Node 2 (ise-node-2) | 10.10.20.78 | Secondary (MNT/PERSONA) |
| Windows AD (windows-ad) | 10.10.20.100 | Identity source (HTTP 200 on :80) |

Admin UI: `http://10.10.20.77` (redirects to HTTPS) — `admin` / `QAWSedrf1234!`.
License: **Evaluation mode, 47 days** at reservation start.

## Access recipe

1. **SSO**: open the reservation link with `?silent_login_idp=cisco&silent_login_account=DevNet`; if the Stack Automation session is cold you must complete id.cisco.com (Okta) login with the Cisco ID. The silent-login params alone do NOT skip it.
2. **VPN (AnyConnect)**: `devnetsandbox-usw1-reservation.cisco.com:20114`, user `tyrelcb`, per-reservation password (see Credentials below). Routes: `10.10.20-24.0/24`, `10.17.248.0/24`, `172.16.30.0/24`, `192.168.254.0/24`.
3. **ISE Admin**: `https://10.10.20.77/admin/` (self-signed cert).

## Credential harvesting (no eyeballing the eye icons)

The Access Details cards mask secrets, and the reveal toggle is hover-gated React.
Reliable trick (CDP): hook `navigator.clipboard.writeText`, click every copy button
(phosphor "copy" icon path `M216,28H88A12...`) inside the cards — the *plaintext* of
every field lands in the hook. Node IPs come clean from
`GET /api/spaces/DevNet/environments/<envId>/introspection` with
`Authorization: Bearer <localStorage.loginResponse access_token>`.

## Findings / gotchas

- **Web SSO form**: Okta "Next" is an `input[type=submit]` (no `<button>`); set the value with the native HTMLInputElement setter + `input` event, then click via `Input.dispatchMouseEvent` coords (React ignores `.click()` on some widgets).
- **Self-signed cert**: on the agent-browser, type `thisisunsafe` on the interstitial to proceed.
- **Login form**: POSTs go to `/admin/LoginAction.do` with OWASP CSRFGuard (`OWASP_CSRFTOKEN=...`, token embedded in `login.jsp` as `name="CSRFTokenNameValue"`); the UI also requires the dojo-set fields, and there is Referer validation — scripted curl login returns 400 "Invalid request" unless the full token+referer dance is replicated. UI login in a real browser is simplest; session cookie is `MNTLA_JWT_TOKEN` (httpOnly JWT).
- **API ports**: ERS (9060/9061) and OPS API (9062) are **not listening** as dedicated
  ports in this build/sandbox — but **both serve on :443** with basic auth. ERS reads/writes
  fully work (needs an `ERS: N` version header — use `ERS: 3` for internaluser writes).
  OPS is thin: only `/api/v1/endpoint` answers; most other `/api/v1/*` paths 404.
  The rich UI backend (`/admin/api/*`) is session-cookie + CSRFGuard only, not basic-auth reachable.
- **openconnect `--background`** still makes the foreground call hang/timeout — verify with `pgrep -a openconnect` + `ip route | grep tun0`.

## Capabilities tour (what's actually here)

- **ERS**: 25,001 internal users, 1,009 identity groups, 16 TrustSec SGTs, 9 authorization
  profiles, NAD CRUD — all exercised (create/read/update/delete an internal user + NAD).
- **Live RADIUS**: registered VPN client as a NAD, `radtest` → **Access-Accept** (correct
  creds) / **Access-Reject** (wrong), each visible in Operations › RADIUS › Live Logs.
  Gotchas: user must be `changePassword:false`; NAD IP must be the `tun0` src.
- **Policy**: 1 Default policy set (Default Network Access). **676** Cisco-provided profiling
  policies. Full default **Posture** policy (AntiMalware/AppVis/Firewall, Win+Mac).
- **pxGrid**: Direct Service running on :8905 (no registered subscriber). Segmentation
  Policy Service persona disabled → SGTs defined but not enforced.
- **AD join FAILS**: documented join creds (`Administrator`/`PythonRocks`, and DevNet
  `C1sco12345`) both rejected — "Cannot retrieve TGT … invalid username or password".
  The blueprint publishes no separate AD-join secret; treat AD integration as unavailable.
- Full detail in [`ise-sandbox.md`](ise-sandbox.md).

## Files

- `ise-sandbox.md` — raw access details + credentials (this reservation).
- Skills: `~/.langbang/skills/ise-sandbox-access/SKILL.md` (reusable procedure).
- Sibling labs: `~/projects/cisco-aci-lab`, `~/projects/iosxe-lab`, SD-WAN docs.

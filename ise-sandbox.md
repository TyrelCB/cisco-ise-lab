# ISE Sandbox — reservation access details (20261105220143)

Env id: `ewFosboPkwCl` · Space: DevNet · On Demand · Security / ISE
Created 2026-11-05 22:01 UTC-ish, runtime 4 days (Extend button available).

## VPN (AnyConnect / openconnect)
- Address: `devnetsandbox-usw1-reservation.cisco.com:20114`
- Username: `tyrelcb`
- Password: `rU1F_3U2Rsw%e`   (contains `%` — quote it)

```
umask 077; printf '%s' 'rU1F_3U2Rsw%e' > /tmp/vpn.pw
sudo -n openconnect --protocol=anyconnect --user=tyrelcb --passwd-on-stdin \
  --background devnetsandbox-usw1-reservation.cisco.com:20114 < /tmp/vpn.pw
# verify: pgrep -a openconnect ; ip route | grep tun0
```
Routes advertised: 10.10.20-24.0/24, 10.17.248.0/24, 172.16.30.0/24, 192.168.254.0/24.

## ISE
- Node 1 (PAN): `http://10.10.20.77` → https → /admin/  (301/302)
- Node 2: `10.10.20.78`
- Username: `admin`
- Password: `QAWSedrf1234!`
- License: Evaluation, 47 days remaining at start.

## Windows AD
- `10.10.20.100` — HTTP 200 on :80, no HTTPS. (Join point / identity source for the demos.)

## Verified
- Both ISE nodes: HTTP 301→https, https /admin/ 302→login. UI login as admin succeeds → Dashboard ("Evaluation Mode 47 Days").
- ERS/OPS ports 9060/9061/9062 not externally listening; scripted curl login to /admin/LoginAction.do returns 400 (CSRFGuard) — use browser UI login.

---

# Capability tour (2026-11-06)

## Version / deployment
- **ISE 3.2.0.542 Patch 2** (confirmed via `show version` over SSH CLI, sshpass admin@10.10.20.77).
- ise-1 = Primary PAN + MNT; ise-2 = Secondary PAN + MNT. Both carry Administration,
  Monitoring, Policy (PSN) and pxGrid personas. `show application status ise` →
  ISE pxGrid Direct Service **running**; Segmentation Policy Service and
  pxGrid Cloud Agent **disabled**.
- License: **Evaluation**, ~47 days.

## APIs (all on 443, basic auth admin:QAWSedrf1234!)
- **ERS** (External RESTful Services) — enabled & functional on 443.
  - `GET /ers/config/internaluser` → **25,001** users (ScaleUser1..N preloaded perf data).
  - `GET /ers/config/identitygroup` → **1,009** groups.
  - `GET /ers/config/networkdevice` → 2 (pez_simulator + langbang-vpn-client).
  - `GET /ers/config/authorizationprofile` → 9.
  - `GET /ers/config/sgt` → **16** TrustSec SGTs defined.
  - **Version-header gotcha:** every ERS call needs an `ERS: N` header.
    `ERS: 4` reads work, but **user create/PUT is buggy on v4** (see below) —
    use **`ERS: 3`** for internaluser POST. Missing header → 415.
- **OPS / Platform / Admin operations API** — enabled on 443 but **thin**:
  only `/api/v1/endpoint` returns 200. `/api/v1/{user,policyset,networkdevice,
  trustsec/sgt,internaluser,authorizeddevice,node/systemHealthSummary}` and
  `/api/v1/{discovery,swagger.json}` all 404. The full UI backend
  (`/admin/api/...`) is session-cookie + CSRFGuard only, not reachable with basic auth.
- **Port 8905** (API gateway) open → 302 to login for basic auth.
- **9060/9061/9062** (dedicated ERS/OPS ports) closed — everything is on 443.

## ERS internal-user CRUD (verified end-to-end)
- POST create user → **201**; GET by name → **200**; PUT → **200**; DELETE → **204**.
- **Gotcha:** a PUT that drops `firstName`/`lastName` (or uses `ERS: 4`) triggers a
  misleading "Password must satisfy the following rules" 400 even when the password is
  compliant. A minimal `ERS: 3` POST with name/enabled/password/passwordIDStore works.
- Password policy on this box: ≥1 lower, ≥1 upper, ≥1 digit, ≥4 chars.

## NAD + live RADIUS authentication test (verified)
1. Registered the VPN client (`192.168.254.11`, the `tun0` src) as a RADIUS NAD via ERS
   legacy schema (POST `/ers/config/networkdevice`, profileName Cisco, shared secret
   `LangBang123!`, NetworkDeviceIPList mask 32) → **201**.
2. `radtest lb-tour3 'Zx9#mQwe45' 10.10.20.77 0 LangBang123!`
   - correct creds → **Access-Accept** (returns ISE `Class` attribute)
   - wrong creds → **Access-Reject**
   - shared secret validated (Message-Authenticator present on every reply).
3. Live Logs (Operations › RADIUS › Live Logs) shows each attempt with Identity,
   Status, Authentication Policy "Default", Authorization Policy "Default".
   - Gotcha: a user created with `changePassword:true` fails RADIUS with a silent
     Access-Reject (PAP can't service a forced password change). Recreate with
     `changePassword:false` → clean Accept.

## Policy
- **Policy Sets**: exactly **1** — "Default" / Default Network Access, condition-less,
  hit counter incremented by the radtests. Deep links into the policy editor render but
  the SPA editor needs full RBAC navigation (raw `#policy/...` hashes bounce to
  "Page not accessible — insufficient privileges" until you enter via the hamburger menu).
- **Profiling**: **676** Cisco-provided profiling policies (2Wire-Device … Android-*).
  Endpoints preloaded (2, both "unknown"). AI Proposals telemetry banner present (3.2 patch 1).
- **Posture**: fully populated default Posture Policy — AntiMalware / AppVis / Firewall
  rules for Windows All and Mac OSX 4.x+, Agent and Temporary (On-Agent) modes.

## pxGrid / TrustSec
- pxGrid Direct Service **running** (port 8905). REST `/pxgrid/3/rest/*` bounces 302 to
  login without a pxGrid cert/subscriber registration (expected — no registered consumer).
- TrustSec: **16 SGTs** defined; Segmentation Policy Service persona disabled, so no live
  SGT/SGA enforcement in the sandbox.

## AD join (attempted, FAILED — sandbox limitation)
- Ext Id Sources › Active Directory › WindowsActiveDirectory (Join Point preloaded,
  domain `lab.devnetsandbox.local`, DC `10.10.20.100`/`WIN-I9LHTNCNB9O`).
- DNS + reachability from ISE confirmed: `ping lab.devnetsandbox.local` → 10.10.20.100 OK.
- Join with documented creds `Administrator` / `PythonRocks` (and DevNet-standard
  `C1sco12345`) both fail: Operation Detail → "Cannot retrieve TGT for account
  Administrator@LAB.DEVNETSANDBOX.LOCAL, invalid username or password … this error might
  occur due to replication errors". The blueprint's published join password is stale /
  the account is not usable for joining; only 6 secrets are exposed on the Access Details
  cards (VPN addr/user/pw, node host/user/pw) — no separate AD-join secret is published.
  Not fixable from ISE; treat AD integration as unavailable in this reservation.

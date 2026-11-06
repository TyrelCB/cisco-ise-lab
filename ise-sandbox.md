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

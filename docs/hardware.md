# Hardware

Two repurposed Dell OptiPlex desktops, deliberately split by role: one quiet,
low-power machine that runs 24/7, and one older, louder machine kept for
on-demand work.

## Machines

| Machine | Role | Status |
|---|---|---|
| Dell OptiPlex Micro | Primary server: the whole Docker stack (Jellyfin, \*arr apps, qBittorrent behind the VPN, Immich) | Always on |
| Dell OptiPlex 7010 | Spare node, under evaluation as an on-demand backup/NAS box | Powered off by default |

### Dell OptiPlex Micro (primary)

- Ubuntu Server 26.04.1 LTS, installed fresh on a 256 GB Kingston SSD (sole boot drive)
- One SATA bay, so internal storage can't grow; extra capacity has to attach over USB 3.0
- Chosen for 24/7 duty: small, quiet, and low idle power draw

### Dell OptiPlex 7010 (spare)

| Component | Spec |
|---|---|
| RAM | 20 GB DDR3 (2 × 8 GB + 1 × 4 GB) |
| GPU | Older AMD GPU (exact model not recorded) |
| Storage | 500 GB Samsung SATA SSD; several free SATA ports |
| Noise / power | Loud (multiple fans) and a much higher idle draw than the Micro, so it is not run 24/7 |

## Spare parts

| Part | Notes |
|---|---|
| 500 GB HDD | Previously the old server's drive; unused |
| NVIDIA GTX 970 | Not installed. Full-size card with external power connectors and an older video engine; the Micro's integrated GPU is the better fit for Jellyfin transcoding |
| SATA-to-USB 3.0 cable | Lets a SATA drive attach to the Micro, which has no free internal bay |

## Design notes

- **Always-on work goes to the quiet, low-power machine.** The louder machine is
  reserved for tasks that don't need to run continuously, such as scheduled
  backups it can be woken for with Wake-on-LAN and then shut down.
- **Media is replaceable, photos are not.** Movies and shows re-download
  through the automated pipeline (see
  [letterboxd-automation.md](letterboxd-automation.md)), so backup capacity
  is better spent on the photo library and service configs than on media.
- **Torrents and media should share one filesystem.** Sonarr and Radarr import
  by hardlink only when both folders are on the same filesystem; across drives
  every import becomes a slow copy that doubles disk use while seeding.

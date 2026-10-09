# Hardware

Two repurposed Dell OptiPlex desktops, deliberately split by role: one quiet,
low-power machine that runs 24/7, and one older, louder machine kept for
on-demand work.

## Machines

| Machine | Role | Status |
|---|---|---|
| Dell OptiPlex 3050 Micro | Primary server: the whole Docker stack (Jellyfin, \*arr apps, qBittorrent behind the VPN, Immich, monitoring) | Always on |
| Dell OptiPlex 7010 | Spare node, planned as an on-demand backup box | Powered off by default |

### Dell OptiPlex 3050 Micro (primary)

| Component | Spec |
|---|---|
| CPU | Intel Core i5-7500T, 4 cores, 35 W |
| RAM | 8 GB |
| Graphics | Intel HD Graphics 630 (Quick Sync / VAAPI), used for Jellyfin hardware transcoding |
| Storage | 500 GB Samsung 870 EVO SATA SSD, internal: OS, Docker data, Immich and the media library on **one filesystem** |
| Free slot | One M.2 slot under the drive bracket. It accepts **NVMe only** (SATA M.2 drives aren't detected) |
| Network | Gigabit Ethernet (Realtek) |
| OS | Ubuntu Server 26.04 LTS, plain ext4 (no LVM) |

The Micro has a single internal SATA bay, which is why storage capacity is the
main constraint here. It was chosen for 24/7 duty: small, quiet, and low idle
power draw.

**Storage history.** The first layout kept the OS on a small 256 GB SSD and the
media on a 500 GB SSD attached over USB 3.0. It worked, but the USB link logged
recurring CRC errors under sustained reads, and the media volume was a
separate mount. Moving the 500 GB SSD inside as the only drive removed the USB
link entirely, and drive errors dropped to zero. See
[lessons-learned.md](lessons-learned.md).

### Dell OptiPlex 7010 (spare)

| Component | Spec |
|---|---|
| CPU | Intel Core i7-3770, 4 cores / 8 threads, 3.4 GHz (77 W class, hence the heat and fan noise) |
| RAM | 20 GB DDR3-1600 (2 × 8 GB + 1 × 4 GB) |
| Firmware | Dell BIOS A29 (the final release), classic BIOS boot rather than UEFI; the CMOS battery is flat and needs replacing to keep settings across power-offs |
| GPU | Older AMD GPU (exact model not recorded) |
| Storage | Free SATA ports and bays; receives the freed 256 GB SSD |
| Noise / power | Loud (multiple fans) and a much higher idle draw than the Micro, so it is not run 24/7 |

## Spare parts

| Part | Notes |
|---|---|
| 256 GB SATA SSD | Freed up when the Micro moved to the 500 GB drive; reserved for the 7010 |
| 500 GB HDD | Unused; a candidate backup target |
| NVIDIA GTX 970 | Not installed. Full-size card with external power connectors and an older video engine; the Micro's integrated GPU is the better fit for Jellyfin transcoding |
| SATA-to-USB 3.0 cable | Handy for migrations and recovery; no longer used for storage |

## Design notes

- **Always-on work goes to the quiet, low-power machine.** The louder machine is
  reserved for tasks that don't need to run continuously, such as scheduled
  backups it can be woken for with Wake-on-LAN and then shut down.
- **Media is replaceable, photos are not.** Movies and shows re-download
  through the automated pipeline (see
  [letterboxd-automation.md](letterboxd-automation.md)), so backup capacity
  is better spent on the photo library and service configs than on media.
- **Torrents and media share one filesystem *and one mount*.** Sonarr and
  Radarr import by hardlink only when both folders are on the same filesystem
  and are reached through the same bind mount inside the container; otherwise
  every import silently becomes a copy.
- **Keep the media storage internal.** USB-attached storage was the least
  reliable part of this build. A SATA SSD in the Micro's one bay is simpler
  and measurably more stable.

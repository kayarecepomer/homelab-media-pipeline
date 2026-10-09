# Lessons learned

Things that broke while building and migrating this setup, what caused them,
and what fixed them. Each one cost real debugging time, so they're written down.

## 1. Hardlinks need one *mount*, not just one disk

Sonarr and Radarr can import a finished download as a hardlink, so the library
file and the torrent file share one copy on disk and seeding costs no extra
space. The settings said hardlinks were on, yet every import was a full copy.

**Cause:** the containers were given two separate bind mounts
(`.../torrents:/data/torrents` and `.../media:/data/media`). Linux treats
different mounts as different devices and refuses to hardlink across them, even
when both sit on the same disk, so the apps silently fell back to copying.

**Fix:** mount the parent once (`${MEDIA_ROOT}:/data`) for qBittorrent, Sonarr
and Radarr. Paths inside the containers stay identical, so no app settings
change. Existing duplicates were merged afterwards by checking each pair was
byte-identical and swapping in a hardlink atomically (24 films, 54 GB
reclaimed).

## 2. USB-attached storage logs CRC errors under load

A SATA SSD on a USB 3.0 adapter ran fine until sustained reads, then logged
`Information unit iuCRC error` and retried. Data was never corrupted (the
checksums matched) but each retry stalled playback, and the drive was slow to
appear at boot.

**Fix:** put the SSD inside the machine. Errors since then: zero. If USB
storage is unavoidable, mount by UUID with a long device timeout and don't
put anything latency-sensitive on it.

## 3. A "full" disk fails long before 100%

ext4 reserves 5% of a volume for root. On a 216 GB drive that is about 10 GB
that normal services can't use, so apps started failing (and Immich's database
crash-looped) while `df` still showed free space. The cleanup that was planned,
deleting the old copy after a migration, was postponed one step too long.

**Fix:** lower the reserve on data-heavy volumes (`tune2fs -m 1`), keep real
headroom, and delete migration leftovers promptly after verifying them.

## 4. Never let containers start on an unmounted drive

If an external data drive isn't mounted at boot, Docker happily starts the
containers against an empty directory, and apps then react to "missing" files.

**Fixes that worked together:**
- make the empty mount point immutable (`chattr +i`), so nothing can write into
  it when the drive is absent;
- bind-mount a small marker file from the drive into each critical container
  with `create_host_path: false`, so the container refuses to start when the
  marker is missing;
- give the mount a generous device timeout.

With the drive now internal this is moot here, but it's the right pattern
whenever data lives on a removable or slow-to-appear device.

## 5. Hardware transcoding on an old integrated GPU

- Enable VAAPI or QSV in Jellyfin and pass `/dev/dri` into the container.
- **HDR tone mapping needs an OpenCL runtime.** In the container image used
  here, 4K HDR files failed with `Failed to get number of OpenCL platforms`
  until the Intel OpenCL add-on (`DOCKER_MODS=linuxserver/mods:jellyfin-opencl-intel`)
  was installed. Dolby Vision and HDR10+ files fall back to the OpenCL path.
- A 7th-gen Intel iGPU tone-maps a **downscaled** 4K stream in real time
  (about 1.3×) but not a full-resolution one (about 0.6×), so set clients to
  1080p for 4K HDR content.
- **Hardware encoders fill the bitrate they're given;** a CPU encoder in CRF
  mode usually produces much less. For a weak client such as an older Roku
  stick, that difference can matter, so disabling *hardware encoding* (while
  keeping hardware decoding and tone mapping) is a useful experiment.

## 6. The VPN's forwarded port changes on every reconnect

With a VPN provider that assigns a new forwarded port per session, qBittorrent
silently becomes unreachable after each reconnect (new magnets stall at
"downloading metadata").

**Fix:** have gluetun push the new port into qBittorrent's API whenever it
changes (`VPN_PORT_FORWARDING_UP_COMMAND`), and enable "bypass authentication
for clients on localhost" in qBittorrent so the call is accepted. See
[`docker-compose.example.yml`](../docker-compose.example.yml).

## 7. Immich: don't point an external library at Immich's own folders

A previous setup had indexed Immich's own `thumbs/` and `library/` folders as
an external library. Immich then tracked its *thumbnails* as photos (about
15,000 assets), and when that path disappeared they were all marked offline and
trashed, leaving the real photos unregistered and the timeline nearly empty.

**Fix:** mount the folder with the real originals **read-only** at a separate
container path and index that as the external library. The mount being
read-only guarantees Immich can't move or delete anything, and its "storage
template" feature only applies to files uploaded through Immich.

## 8. Migration playbook that worked

1. Back up to a **different machine**, as archives that preserve hardlinks and
   structure, and verify by file count and total bytes (not just "no errors").
2. Take a fresh `pg_dumpall` of the Immich database while its web service is
   stopped, and keep the previous nightly dumps.
3. Stop containers in dependency order (apps, then the database last).
4. Install the new OS **without LVM** so the old disk's volume group can't
   clash, keep the same username/UID so file ownership matches, and leave the
   old OS drive untouched as the fallback until everything has run for a few
   days.
5. Restore by streaming the archives back; **pin the Immich image to the
   version in the database dump** before restoring; then verify VPN exit
   address, hardlinks, port forwarding and every web UI.
6. Pin the machine's address in netplan, and clear the stale SSH host key.

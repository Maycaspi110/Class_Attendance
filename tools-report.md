# Tools Report

Technical tools considered for the attendance system and the other teaching features. Every tool suggested for the demo is tested in real life, and the result is written below.

## Summary

| Area | Tool | How tested | Result | Decision |
|------|------|-----------|--------|----------|
| Presence | Bluetooth (Web Bluetooth) | Documentation; iPhone check pending | Not supported on Safari / iOS | **Rejected** |
| Presence | Changing code | Small prototype page | TBD | TBD |
| Presence | QR code | Generate and scan on Android and iPhone | TBD | TBD |
| Presence | GPS (browser geolocation) | In class, hallway and library | TBD | TBD |
| Presence | IP address | University Wi-Fi vs mobile data | TBD | TBD |
| Hosting | HTTPS hosting (GitHub Pages) | Publish a test page | TBD | TBD |
| Output | CSV spreadsheet for the lecturer | Open in Excel, including Hebrew text | TBD | TBD |
| Building | Claude Code (vibe coding) | Build the demo | TBD | TBD |

## Details

### Bluetooth
The Web Bluetooth API works in Chrome on Android, but not in Safari on iOS or in Firefox. The assignment requires the app to work on all smartphones, so Bluetooth is rejected.

### Changing code
TBD

### QR code
TBD

### GPS
Browser geolocation requires HTTPS and the user's permission, and it reports an accuracy value in meters. Indoor accuracy varies, so a radius of about 150 meters is planned. Real-life test: TBD.

### IP address
A web page cannot read the Wi-Fi network or router. The server can see the IP address, but the whole campus shares one network. Real-life test: TBD.

### HTTPS hosting
TBD

### CSV spreadsheet
TBD

### Claude Code
TBD

## Other features (design only, not tested)

- **Real-time comments:** TBD
- **Polls:** TBD
- **ML summary of class video:** transcript of the recording, then a language model to summarize it
- **LLM homework review:** language model that reviews homework and compares it to other submissions

## Notes

- No method is 100% cheat-proof. Known limitations are documented in the design.
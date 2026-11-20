# Tools Report

Technical tools considered for the attendance system and the other teaching features. Every tool suggested for the demo is tested in real life, and the result is written below.

## Summary

| Area | Tool | How tested | Result | Decision |
|------|------|-----------|--------|----------|
| Presence | Bluetooth (Web Bluetooth) | Documentation; iPhone check pending | Not supported on Safari / iOS | **Rejected** |
| Presence | Changing code | Prototype page (code-test.html), 5 manual checks on a PC | All 5 checks passed | **Chosen** |
| Presence | QR code | Prototype page (qr-test.html), scanned with an iPhone and an Android device | Scanned successfully on both devices, with all three QR sizes | **Chosen**, together with the typed code |
| Presence | GPS (browser geolocation) | In class, hallway and library | Works (iPhone, 2 places) | **Chosen:** GPS for the distance check |
| Presence | IP address | University Wi-Fi vs mobile data | Same address in two places | **Not used** as a check (at most a weak hint) |
| Hosting | HTTPS hosting (GitHub Pages) | Publish a test page | Works | **Chosen:** GitHub Pages (works) |
| Output | CSV spreadsheet for the lecturer | Open in Excel, including Hebrew text | Works | **Chosen:** CSV file |
| Hosting | Render (free web service) | The demo opened on a laptop and on phones over the internet | Works. The free server sleeps after about 15 minutes and wakes up in about a minute | **Chosen** for the demo (the university Wi-Fi blocks phone-to-laptop traffic) |
| AI | Google Gemini API (free tier) | Photo count: a classroom photo uploaded from the lecturer page | Returned 48 people for the photo, and the page compared it with the check-ins | **Chosen** for the photo count, the class summary and the homework review |
| AI | Class summary from a recording | A screen recording of about 2 minutes (141 MB), uploaded from the lecturer page | The browser took out the sound (3.7 MB) and Gemini returned a summary | **Chosen** |
| AI | Homework review | A work sent from the homework page with a roster email, then a second work for the same assignment | A review came back, with the comparison to the other work | **Chosen** |

## Details

### Bluetooth
The Web Bluetooth API works in Chrome on Android, but not in Safari on iOS or in Firefox. The assignment requires the app to work on all smartphones, so Bluetooth is rejected.

### Changing code
Tested with a small prototype page that shows the lecturer screen and the student check together. The code is calculated from a secret and the current time slot (30 seconds), and the previous code is also accepted as a grace period.

| Check | Expected | Result |
|-------|----------|--------|
| Enter the current code | Accepted | Passed |
| Enter the previous code | Accepted (grace period) | Passed |
| Enter a code two changes old | Rejected | Passed |
| Enter a random code | Rejected | Passed |
| Code changes on time | Changes every 30 seconds | Passed |

**Decision:** a typed code that changes every 10-30 seconds, with the previous code accepted.

**Limitation:** a code can be photographed and sent to a friend during its short validity. This is why the location check and the lecturer flag are also used. In the real system the code will be generated on the server, so the secret is not exposed in the browser.

### QR code
Tested with a small prototype page (qr-test.html) that shows a QR code containing a link with the current code. The QR code changes together with the changing code, and the user can choose between a link and a plain text version. The QR code is generated with the open-source library qrcode-generator (MIT license), so no QR code was written from scratch.

| Device | Sizes tested | Distances tested | Result |
|--------|--------------|------------------|--------|
| iPhone | Small, Medium, Large | About 0.5 m, 1 m and 5 m | Scanned successfully, link opened |
| Android device | Small, Medium, Large | Several distances, not measured exactly | Scanned successfully, link opened |

The test pages are in the `tests` folder (`code-test.html` and `qr-test.html`), and the screenshots of the results are in the `evidence` folder.

**Notes:**
- The link in the prototype points to a placeholder domain (example.com), so the opened page shows a documentation notice. This is expected. In the real system the link will point to our own HTTPS page.
- The tests were done on a laptop screen. The classroom board is much larger, so scanning from a distance should be easier. This will be checked in class.
- A QR code can be photographed and shared, just like a typed code. The protection is the same: the code changes every 10-30 seconds, the location check, and the lecturer flag.

**Decision:** QR code is supported together with the typed code. For the demo, the typed code is enough.

### GPS
Browser geolocation requires HTTPS and the user's permission, and it reports an accuracy value in meters. Indoor accuracy varies, so a radius of about 150 meters is planned. GPS (browser geolocation). Tested on one iPhone with the test page (tests/location-test.html) over HTTPS. Two measurements were taken, on different days: in the classroom (accuracy 13 m) and in the library (accuracy 9 m). The distance between the two places, calculated from the coordinates, was about 175 m. The accuracy of each measurement was much smaller than this distance, so GPS can tell the two places apart. Only one phone and one point in each place were tested. Other points inside the classroom and Android phones were not tested. Because the library is only about 175 m from the classroom, a radius of 150 m is too close to the library, and a radius of 50-100 m should be considered. The final radius is still to be decided. The classroom location is not fixed in the system: each lecturer saves it by pressing Start in their own classroom, so the system works in any classroom.

### IP address
A web page cannot read the Wi-Fi network or router. The server can see the IP address, but the whole campus shares one network. IP address. The test page reads the public IP address of the phone. In the classroom and in the library (both on the university Wi-Fi) the address was the same, so an IP check cannot tell the two places apart. On a different network (not on campus) the address was different, so the IP can at most show that a phone is on the campus network. The phone settings showed that the local address of the phone inside the campus network was different in the two places, but a web page cannot read it. Decision: the IP is not used as a check, and at most it can be a weak hint.

### HTTPS hosting
HTTPS hosting (GitHub Pages). The test page was published with GitHub Pages and is served over HTTPS (Enforce HTTPS is on). It opened on a laptop and on an iPhone. On both devices the browser asked for location permission and returned a measurement. This works only because the page is served over HTTPS. Accuracy was about 10 m on the phone and about 183 m on the laptop (which has no GPS).

### CSV spreadsheet
CSV spreadsheet. A sample attendance file (tests/attendance-sample.csv; it was opened in Excel in its first version with the columns Email, Name, Status, Check-in time, Distance from classroom, Note, and it was updated later with the start and end check-in columns and the comment; four made-up students with the statuses Present, Flagged and Absent) was opened by double-click in Microsoft Excel on Windows. Each column appeared in its own column and all four rows were shown correctly. The sheet was displayed right to left because of the Hebrew language settings, and the column widths had to be widened to read the long headers. Names written in Hebrew were not tested.

### Render hosting
The first plan was GitHub Pages, but the demo needs a server (codes, check-ins, AI calls), and the phones could not reach a laptop on the university Wi-Fi, because the network blocks traffic between devices. The demo therefore runs as a free web service on Render, which gives an HTTPS address that works from any phone. The free service sleeps after about 15 minutes without use and wakes up in about a minute, so the site should be opened a few minutes before the demo. The data is kept in memory and is lost when the server sleeps, so the roster is uploaded again. The AI key is kept only in the Render settings.

### AI (Google Gemini)
The AI features use the Gemini API of Google, on the free tier, because there is no budget for a paid API plan. The server calls the API with a key that is kept only in the server settings, so the phones never see it. All three features use the same key: counting people in a photo, summarizing a class recording and reviewing homework. The model name is a setting, because Google replaces models over time: the first model I used (gemini-2.5-flash) was no longer available and was replaced.

**Photo count test:** the lecturer page sent a classroom photo and Gemini returned 48 people, which the page compared with 1 check-in. The count is rough, so it is only a warning for the lecturer.

**Limits and risks:** the free tier has request limits per minute and per day, and an answer can take several seconds. The photo, the sound of recordings and the works are sent to Google, so the demo uses sample data and not real students' work. The terms of the free tier were not checked in detail. The homework review was tried with a real student email and works. The first version of the class summary sent the whole video and was refused as too big, and a slow answer stopped the request: so the sound is taken out in the browser, and the AI works in the background.

## Other features
- **Student comments:** implemented, a text box in the end-of-class check-in
- **Polls:** implemented, a question with 2-6 options
- **Class summary and homework review:** implemented with the AI above
- **Students uploading their own summaries:** dropped



## Notes

- No method is 100% cheat-proof. Known limitations are documented in the design.
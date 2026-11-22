# Class Attendance & Teaching Tool

A simple web-based tool for teaching in class. Students use it from any smartphone through the browser, with nothing to install.

> Course: Introduction to Software Engineering, Ariel University
> Ex2 - Vibe Coding & Deep Designing | Author: May Caspi

**Live demo:** https://class-attendance-ogqg.onrender.com

(Students: open it on a phone and press *I am a student*. Lecturer: press *I am a lecturer*, the password is given in class. The free server sleeps when it is not used, so the first visit can take about a minute.)

**The app and how to run it:** [demo/README.md](demo/README.md)

**Documents:** [SoW](SoW.md), [SRS](SRS.md), [use cases](use-cases.md), [components](components.md), [diagrams](diagrams.md), [testing strategy](testing-strategy.md), [tools report](tools-report.md), [demo script](demo-script.md), [conclusion](conclusion.md)

## Problem

Taking attendance in class is slow and manual, and current online teaching tools are too complicated. The goal is a simple tool that works in a real classroom, on students' own phones.

## Goal

Design an end-to-end web application for teaching in class. The assignment is mainly a design challenge, and the main feature is **automatic attendance**.

## How it works

![How attendance works](attendance-flow.png)

0. Everyone starts from one home page with two tiles: student and lecturer. The student menu has Mark attendance and Homework review. The lecturer menu (with the lecturer password) has Course roster, Attendance & results, Classroom screen, Photo count, Class summary and Poll.
1. The lecturer uploads the course roster once, and opens attendance from their phone inside the classroom. The system saves that location as the classroom location.
2. A code (also shown as a QR code) appears on the classroom screen and changes every 10-30 seconds.
3. A student on the roster opens the web page on their phone, enters their email and the code (or scans the QR code), and is marked present.
4. At the end of the class there is a second check-in. Students can write a comment about the lesson, and a student who came late or left early is shown as such.
5. The lecturer can take a photo of the classroom. An AI counts the people, and the number is compared with the check-ins.
6. The lecturer receives an online/offline spreadsheet with the attendance details.

## Presence checks

- **Course roster:** only registered students can mark attendance, so students from other classes are excluded.
- **Code on the classroom screen:** proves the student can see the screen in the room.
- **GPS location:** the student must be within about 150 meters of the classroom, which filters out students in far places such as the library.
- **Flag for the lecturer:** if the code is valid but the location is far, the student is flagged, not rejected. The lecturer decides.
- **Photo count:** the number of people in a photo of the classroom is compared with the number of check-ins. It is a rough count and only a warning. The photo is not saved.

No method is 100% cheat-proof, and known limitations will be documented in the design.

## Scope

- **Implemented in the demo:**
  - Attendance: roster, changing code, location check, two check-ins (start and end of class), lecturer spreadsheet
  - Student comments at the end check-in
  - Photo headcount (AI) as a second check
  - Lecturer polls
  - Lecturer-only AI summary of a class recording (a screen or Zoom recording, or a public YouTube link)
  - Homework page: a student sends a work and gets an AI review once a day. When at least 8 students sent their work, a student can compare their work with a general overview of the class, once a day
- **AI:** Google Gemini (free tier), used from the server. The key is kept only in the server settings.
- **Not included:** integration with Moodle, Zoom, or personal information systems; students uploading their own summaries; polls sent by email
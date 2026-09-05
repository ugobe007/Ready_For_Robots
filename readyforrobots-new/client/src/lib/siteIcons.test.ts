*** Begin Patch
*** Update File: readyforrobots-new/client/src/lib/siteIcons.test.ts
@@
     const landing = readFileSync(
       join(here, "../components/JobsLanding.tsx"),
       "utf8"
     );
@@
     expect(landing).toMatch(/SiteIcon/);
     expect(landing).toMatch(/icon="truck"/);
     expect(landing).toMatch(/icon="handshake"/);
+    // Landing should override truck/handshake with the purple art/stroke
+    expect(landing).toMatch(/#7C3AED/);
*** End Patch

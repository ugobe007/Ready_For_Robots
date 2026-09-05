/*** Begin Patch
*** Update File: readyforrobots-new/client/src/components/JobsLanding.tsx
@@
 function LandingDoor({
@@
-  return (
-    <a
-      href={href}
-      data-landing-option={option}
-      className={`rfr-landing-door rfr-landing-door--${option}`}
-    >
-      <span className="rfr-landing-door-mark" aria-hidden="true">
-        <SiteIcon id={icon} scale={LANDING_DOOR_ICON_SCALE} />
-      </span>
+  const isPurpleIcon = icon === "truck" || icon === "handshake";
+  const iconFill = isPurpleIcon ? "#7C3AED" : undefined;
+  const iconBackground = isPurpleIcon ? "transparent" : undefined;
+
+  return (
+    <a
+      href={href}
+      data-landing-option={option}
+      className={`rfr-landing-door rfr-landing-door--${option}`}
+    >
+      <span className="rfr-landing-door-mark" aria-hidden="true">
+        <SiteIcon
+          id={icon}
+          scale={LANDING_DOOR_ICON_SCALE}
+          fill={iconFill}
+          background={iconBackground}
+        />
+      </span>
*** End Patch

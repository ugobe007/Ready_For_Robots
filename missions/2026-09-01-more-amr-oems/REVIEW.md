# More AMR OEM review

**Date:** 2026-09-01
**Branch:** `cursor/more-amr-oem-catalog-009b`
**Score:** critic corpus PASS (35/35). Fixtures 8/8 PASS. All six operator URLs have n≥1 named products.

This is the review. `report.md` in this folder has the product table.

I fetched the live sites. curl gets 403 on teradyne.com (Cloudflare). WebFetch still returned the AMR hub copy, and that page names one SKU. XPENG's homepage is cars. IRON is named on `/au/explore/xpeng_ai_robot_iron` and on XPENG news pages, not on the EV catalog.

## What the sites actually name

**Galaxea Dynamics.** https://galaxea-dynamics.com/ Products menu names R1 Pro, R1 Lite, Kengo, and A1 Z. R1 Pro is a 7-DOF dual-arm wheeled humanoid. R1 Lite is a 6-DOF general mobile manipulation platform. Kengo is a bipedal embodied-AI robot. A1 Z is a desktop arm. Lite-T is a teleop module for R1 Lite. G1 Gripper and the VLA unit are accessories. Those stay out.

**XPENG.** https://www.xpeng.com/ is Smart Electric Vehicles. G6 / P7 / G9 stay cars. The robot page https://www.xpeng.com/au/explore/xpeng_ai_robot_iron names IRON as a humanoid AI robot. I did not add PX5 or "XPENG Humanoid".

**ARA Robotics.** http://ararobotics.eu/ (https://ararobotics.eu/en/) names ARI and Petek. ARI is an autonomous floor maintenance robot. Petek is a charging and water-refill station for ARI, so it stays unclassified. I did not dump cleaning onto Petek.

**Cartken.** https://www.cartken.com/ names Cartken Hauler, Cartken Courier, and Cartken Mover. All three are outdoor AMRs on that page. Hauler Temperature Control is a Hauler option, not a separate SKU. The old jobs-seed row named "Cartken" is gone.

**MiR.** https://mobile-industrial-robots.com/ names MiR250, MiR600, MiR1350, and MiR1200 Pallet Jack. MC250 / MC600 are MiR Go partner modules. Workbook leftovers MiR1000 and MiR500 are still in the merged catalog. They are not on the live homepage.

**Teradyne.** https://www.teradyne.com/robotics/autonomous-mobile-robots/ names MiR1200 Pallet Jack. It talks about MiR AMRs as a range and does not name MiR250 / MiR600 / MiR1350. I did not copy those from the MiR catalog. Test-equipment SKUs stay out.

## Class

Work language and hardware copy on the product, not the company. Galaxea R1 Lite stays mobile_manipulator. R1 Pro and Kengo stay humanoid. Cartken Courier stays amr because the page calls it an outdoor AMR. ARI is cleaning. Petek has no FIND class.

## Thin / unclassified

- Petek: named docking station, not a robot class.
- A1 Z, Lite-T, G1 Gripper, VLA All-in-One Unit: arm or accessory, not a FIND robot.
- Cartken Hauler Temperature Control: configuration of Hauler.
- MiR1000 / MiR500: workbook rows, not named on the live homepage.
- Teradyne does not name MiR250 / MiR600 / MiR1350.

## Extract

Listing hints include Galaxea product paths, XPENG `/au/explore/xpeng_ai_robot_iron`, ARA `/en/ari` and `/en/petek`, MiR robot paths, and the Teradyne AMR hub. `oem_sku` replaces the index dump on these hosts so PX5 and the Cartken company dump cannot sit next to page names. xpeng.com is no longer a junk lookup host. The EV catalog is still filtered as vehicles.

Catalog cache is `ontology/mixed_oem_sku_catalog.v1.json`. Live extract still wins.

## What stayed green

VinMotion still Motion 1 humanoid / Motion 2 unclassified. Tennant 5. SEER 7. Pudu mixed serving / cleaning / humanoid. Empty known OEM is still a break. No Fly on this branch. Do not merge leftover #197/#202. Draft #206 Dexory dump-class is separate.

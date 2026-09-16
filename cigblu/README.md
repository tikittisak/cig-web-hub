# CIG Internal Hub

ศูนย์สื่อสาร **IT ↔ MKT** สำหรับเว็บ `cigblu.com` — เว็บภายในที่ **มิเรอร์โครงหน้าเว็บจริง**
เพื่อบอกในที่เดียวว่าแต่ละหน้า *ต้องแก้อะไร · โหลด resource อะไร · สถานะแค่ไหน*

## เปิดใช้งาน
- หน้าเว็บ (GitHub Pages): เปิด `index.html` = Dashboard รวมทุกหน้า
- แต่ละหน้ามิเรอร์ URL จริง เช่น เว็บจริง `/products/refrigeration` → hub `products/refrigeration/`

## หลักการ
- hub เป็น **ชั้น index** ไม่เก็บไฟล์เนื้อหาซ้ำ (กันข้อมูลล้า) — ปุ่มโหลดชี้ไฟล์จริงใน repo เว็บ
- **โครง** มาจาก target tree (migration-map + nav-structure) · **สถานะ** มาจากเว็บที่ IT ขึ้นจริง

## แต่ละหน้ามี 4 บล็อก
1. Change notes — สิ่งที่ต้องแก้ 2. Resource downloads — ไฟล์ให้ IT โหลด
3. สถานะงาน 4. ลิงก์อ้างอิง (Figma / live / repo)

## ยังไม่ทำในรอบ scaffold นี้
- Global shell (nav/footer) → IT ขึ้นเสร็จแล้ว ยังไม่จำเป็น

## Sync log
- 2026-09-16: เพิ่ม 27 model pages (Coils/Coating/AHU/Refrigeration/Marine) จาก `cib-website` (repo dev จริงของ www.cigblu.com, `site/products/library.json`) — เนื้อหาเขียนเสร็จพร้อม deploy แล้วทุกหน้า เช็คสดยัง 404 ทั้ง web.cigblusolutions.com และ www.cigblu.com รอ IT publish เท่านั้น ไม่ใช่รอเนื้อหา
- 2026-09-16: เพิ่มอีก 4 solution pages (coil-replacement-ahu-renovation, cold-room-design-installation, smart-solutions-iot, product-development) จาก `cib-website` `site/solutions/library.json` เหตุผลเดียวกัน — ยังไม่พบ content สำหรับ "BluSolutions" (overview) หรือ "M&E Design & Solutions" ใน cib-website (M&E ตัวจริงชี้ออกไปเพจ Facebook `cigmesolutions` จากหน้า catalog ของ cigblu.com เอง ดูเหมือนเป็นแบรนด์/ทีมแยกต่างหาก ไม่ใช่ของที่จะย้ายเข้ามา)

> สถานะเป็นเว็บภายใน — ตั้ง `noindex` ทุกหน้า ไม่ให้ search engine เก็บ

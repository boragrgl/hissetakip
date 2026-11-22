#!/usr/bin/env python3
"""Siteyi hazırlar.
- site/data/sonuc.json : robotun çıktısı (repoda yayınlanan site bunu fetch ile okur)
- site/hisse-takip.html : veri gömülü tek dosya (yan panel / artifact için)
Kullanım: python3 robot/build_site.py site/data/sonuc.json site
"""
import json, os, shutil, sys

src, site = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "site")
os.makedirs(os.path.join(site, "data"), exist_ok=True)
dst = os.path.join(site, "data", "sonuc.json")
if os.path.abspath(src) != os.path.abspath(dst):
    shutil.copyfile(src, dst)
html = open(os.path.join(site, "hisseler.html"), encoding="utf-8").read()
data = json.dumps(json.load(open(src, encoding="utf-8")), ensure_ascii=False).replace("</", "<\\/")
html = html.replace("<script>\n{", "<script>window.__TA_DATA__=" + data + ";</script>\n<script>\n{", 1)
open(os.path.join(site, "hisse-takip.html"), "w", encoding="utf-8").write(html)
print("ok", os.path.join(site, "hisse-takip.html"))

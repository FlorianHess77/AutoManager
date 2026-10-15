"""Navigation: Android-Zurück, Fenster, Vollbild-Ebenen, Aktualisieren, Kaltstart, QR-Link.

python3 tests/test_nav.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

IMG = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPSc0MDAnIGhlaWdodD0nMzAwJz48cmVjdCB3aWR0aD0nNDAwJyBoZWlnaHQ9JzMwMCcgZmlsbD0nI2Q0NDAzYScvPjwvc3ZnPg=="

SWIPE = """(dy)=>{const hd=document.querySelector('#sheet .sheet-head');const r=hd.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;
 const t=(yy)=>new Touch({identifier:1,target:hd,clientX:x,clientY:yy});
 hd.dispatchEvent(new TouchEvent('touchstart',{touches:[t(y)],changedTouches:[t(y)],bubbles:true,cancelable:true}));
 for(let i=1;i<=6;i++)hd.dispatchEvent(new TouchEvent('touchmove',{touches:[t(y+dy*i/6)],changedTouches:[t(y+dy*i/6)],bubbles:true,cancelable:true}));
 hd.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[t(y+dy)],bubbles:true,cancelable:true}));}"""


async def main():
    c = H.Check('Navigation')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base)
        ev = page.evaluate
        cid = await ev("myCars()[0].id")

        # Seite → Seite → Zurück
        await H.go(page, '#/tools'); await H.go(page, f'#/car/{cid}')
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq(await ev("location.hash"), '#/tools', 'Zurück von Auto → Werkstatt')

        # Fenster offen → Zurück schließt nur das Fenster
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq((await ev("sheetOpen"), await ev("location.hash")), (False, '#/tools'), 'Zurück schließt Fenster, Seite bleibt')

        # Bild-Vollansicht über einem Fenster: Zurück schließt nur das Bild
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await ev(f"(()=>{{const i=new Image();i.src={IMG!r};A.photoView({{}},i)}})()"); await page.wait_for_timeout(200)
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq((await ev("$('#lightbox').classList.contains('hidden')"), await ev("sheetOpen")), (True, True),
             'Zurück bei Bild über Fenster: Bild zu, Fenster bleibt offen')
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq(await ev("sheetOpen"), False, 'zweites Zurück schließt das Fenster')

        # Zuschneiden (Vollbild) über dem Auto-Formular: Zurück bricht nur das Zuschneiden ab
        await ev(f"carForm('{cid}')"); await page.wait_for_timeout(200)
        await ev(f"(()=>{{window._crop=openCropper({IMG!r});return 1}})()"); await page.wait_for_timeout(300)
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq((await ev("$('#cropper').classList.contains('hidden')"), await ev("sheetOpen")), (True, True),
             'Zurück beim Zuschneiden: Zuschneiden zu, Formular bleibt')
        await ev("sheetOpen&&closeSheet()"); await page.wait_for_timeout(300)

        # Beschriften (Vollbild) → Zurück
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await ev(f"(()=>{{window._an=annotate({IMG!r});return 1}})()"); await page.wait_for_timeout(300)
        await page.go_back(timeout=3000, wait_until="commit"); await page.wait_for_timeout(300)
        c.eq((await ev("!!document.getElementById('anno')"), await ev("sheetOpen")), (False, True),
             'Zurück beim Beschriften: Beschriften zu, Formular bleibt')
        await ev("sheetOpen&&closeSheet()"); await page.wait_for_timeout(300)

        # Fenster am Titel nach unten wegziehen
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await ev(f"({SWIPE})(400)"); await page.wait_for_timeout(500)
        c.eq(await ev("sheetOpen"), False, 'Wischen am Titel schließt das Fenster')
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await ev(f"({SWIPE})(30)"); await page.wait_for_timeout(500)
        c.eq(await ev("sheetOpen"), True, 'kurzes Wischen lässt das Fenster offen')
        await ev("closeSheet()"); await page.wait_for_timeout(300)

        # Aktualisieren bleibt auf der Seite (auch Startseiten-Reiter)
        await H.go(page, '#/stats')
        await page.reload(); await H.ready(page)
        c.eq(await ev("location.hash"), '#/stats', 'Aktualisieren bleibt auf Statistik')
        await H.go(page, '#/home'); await ev("A.homeTab({t:'log'})")
        await page.reload(); await H.ready(page)
        c.eq(await ev("homeTab"), 'log', 'Aktualisieren bleibt im Verlauf-Reiter')

        # Kaltstart (neuer Tab) → Übersicht; QR-Link → Auto
        p2 = await ctx.new_page(); p2.errors = []
        await p2.goto(base + 'index.html#/stats'); await H.ready(p2)
        c.eq((await p2.evaluate("location.hash"), await p2.evaluate("homeTab")), ('#/home', 'ov'), 'Kaltstart landet in der Übersicht')
        await p2.close()
        p3 = await ctx.new_page()
        await p3.goto(base + f'index.html#/car/{cid}'); await H.ready(p3)
        c.eq(await p3.evaluate("location.hash"), f'#/car/{cid}', 'QR-Link öffnet das Auto')
        c.eq(await p3.evaluate("$('#title').textContent"), await ev(f"dispName(car('{cid}'))"), 'QR-Link zeigt Autoname')
        await p3.close()
        c.eq(page.errors, [], 'keine JS-Fehler')
        await b.close()
    return c.done()

if __name__ == '__main__':
    H.run(main)

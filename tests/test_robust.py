"""Robustheit: Eingaben-Rückgängig, Tastatur, Fehleransicht, Update-Hinweis.

python3 tests/test_robust.py
"""
import os, sys, shutil, tempfile, re
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright


async def main():
    c = H.Check('Robustheit')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base)
        ev = page.evaluate
        cid = await ev("myCars()[0].id")

        # --- Formular aus Versehen geschlossen → Rückgängig holt die Eingaben zurück
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await page.fill('#fEntry [name=title]', 'Querlenker getauscht')
        await page.mouse.click(195, 20)  # dunkler Bereich über dem Fenster
        await page.wait_for_timeout(400)
        c.eq(await ev("sheetOpen"), False, 'Tippen neben das Fenster schließt es')
        c.ok('Eingaben verworfen' in (await ev("$('#toast').textContent")), 'Hinweis „Eingaben verworfen“')
        await page.click('#toast .tbtn'); await page.wait_for_timeout(300)
        c.eq(await ev("sheetOpen&&$('#fEntry [name=title]').value"), 'Querlenker getauscht', 'Rückgängig stellt das Formular mit Eingaben wieder her')
        # danach normal speichern klappt
        await page.click('#sheet .sheet-foot .btn.primary'); await page.wait_for_timeout(500)
        c.ok(await ev("S.entries.some(e=>e.title==='Querlenker getauscht')"), 'wiederhergestelltes Formular speichert')
        c.ok('Eingaben verworfen' not in (await ev("$('#toast').textContent")), 'nach Speichern kein „verworfen“-Hinweis')

        # Unverändertes Formular schließen → kein Hinweis
        await page.wait_for_timeout(2500)
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        await page.mouse.click(195, 20); await page.wait_for_timeout(300)
        c.ok(not (await ev("$('#toast').classList.contains('show')&&$('#toast').textContent.includes('verworfen')")), 'unverändert: kein Hinweis')

        # --- Tastatur: Fenster wird kleiner, Speichern bleibt sichtbar, untere Leiste weg
        await ev(f"fuelForm(null,'{cid}')"); await page.wait_for_timeout(200)
        await page.focus('#fFuel [name=note]')
        await page.set_viewport_size({'width': 390, 'height': 450}); await page.wait_for_timeout(600)
        foot = await ev("(()=>{const r=$('#sheet .sheet-foot').getBoundingClientRect();return r.bottom<=innerHeight+1&&r.top>0})()")
        c.ok(foot, 'Speichern-Knopf über der Tastatur sichtbar')
        c.ok(await ev("document.body.classList.contains('kb')"), 'Tastatur erkannt (untere Leiste ausgeblendet)')
        inp = await ev("(()=>{const r=document.activeElement.getBoundingClientRect(),f=$('#sheet .sheet-foot').getBoundingClientRect();return r.top>=0&&r.bottom<=f.top+1})()")
        c.ok(inp, 'aktives Eingabefeld sichtbar')
        await page.set_viewport_size({'width': 390, 'height': 844}); await ev("document.activeElement.blur()"); await page.wait_for_timeout(500)
        c.ok(not await ev("document.body.classList.contains('kb')"), 'Tastatur zu: Leiste wieder da')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)

        # --- Fehler in einer Ansicht → Hinweis statt leerer Seite
        await ev("window._vs=viewStats;viewStats=()=>{throw new Error('Testfehler')};1")
        await H.go(page, '#/stats')
        txt = await ev("$('#view').textContent")
        c.ok('konnte nicht angezeigt werden' in txt, 'Fehleransicht statt leerer Seite')
        await ev("viewStats=window._vs;1"); await H.go(page, '#/home')
        await b.close()

        # --- Update-Hinweis: Server hat neuere Version als die geladene Seite
        tmp = tempfile.mkdtemp()
        for f in ['index.html', 'sw.js', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png']:
            shutil.copy(os.path.join(H.ROOT, f), tmp)
        H.ROOT_SAVE = H.ROOT
        H.ROOT = tmp
        base2, srv2 = H.serve()
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base2, sw=True)
        await page.wait_for_function("navigator.serviceWorker.controller!==null", timeout=10000)
        await page.wait_for_timeout(800)
        c.ok(not await page.evaluate("!!document.getElementById('updBar')"), 'gleiche Version: kein Update-Hinweis')
        ip = os.path.join(tmp, 'index.html')
        t = open(ip, encoding='utf-8').read()
        n = int(re.search(r"APP_VER='garage-v(\d+)'", t).group(1))
        open(ip, 'w', encoding='utf-8').write(t.replace(f"APP_VER='garage-v{n}'", f"APP_VER='garage-v{n + 1}'"))
        await page.evaluate("updLast=0;checkUpdate()")
        try:
            await page.wait_for_selector('#updBar', timeout=10000)
            c.ok(True, 'neue Version: Hinweis „Neu laden“')
        except Exception:
            c.ok(False, 'neue Version: Hinweis „Neu laden“')
        c.eq(page.errors, [], 'keine JS-Fehler')
        await b.close()
        H.ROOT = H.ROOT_SAVE
    return c.done()

if __name__ == '__main__':
    H.run(main)

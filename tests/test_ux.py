"""Bedienung: Löschen mit Rückgängig, eigene Dialoge, Standardwerte, Leere-Zustände, Tippflächen.

python3 tests/test_ux.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

SMALL = """()=>[...document.querySelectorAll('#view button,#view .btn,#view .chip,#sheet button,nav.tabs button,.fab')].filter(b=>{const r=b.getBoundingClientRect();return r.width&&r.height&&getComputedStyle(b).visibility!=='hidden'})
 .map(b=>{const r=b.getBoundingClientRect();return{t:(b.textContent||b.getAttribute('aria-label')||b.className).trim().slice(0,30),w:Math.round(r.width),h:Math.round(r.height),c:b.className}})
 .filter(x=>(x.h<40||x.w<40)&&!/linkbtn|h2a|ac-item|tag/.test(x.c))"""


async def main():
    c = H.Check('Bedienung')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base)
        ev = page.evaluate
        dialogs = []
        page.on('dialog', lambda d: dialogs.append(d.message))
        cid = await ev("myCars()[0].id")

        # Löschen ohne Rückfrage, Rückgängig stellt wieder her
        eid = await ev(f"S.entries.find(e=>e.carId==='{cid}'&&e.category!=='Pickerl').id")
        n0 = await ev("S.entries.length")
        await ev(f"entryForm({{id:'{eid}'}})"); await page.wait_for_timeout(200)
        await page.click('#sheet .sheet-foot .btn.danger'); await page.wait_for_timeout(400)
        c.eq((await ev("S.entries.length"), await ev("sheetOpen")), (n0 - 1, False), 'Eintrag gelöscht, Fenster zu – ohne Rückfrage')
        c.eq(dialogs, [], 'kein Browser-Popup')
        c.ok(await ev("$('#undo').classList.contains('show')"), 'Rückgängig-Leiste sichtbar')
        await page.click('#undoBtn'); await page.wait_for_timeout(400)
        c.eq(await ev(f"!!S.entries.find(e=>e.id==='{eid}')"), True, 'Rückgängig stellt den Eintrag wieder her')

        # Lagerbestand über eigenes Fenster
        await H.go(page, '#/inv')
        fid = await ev("S.inventory.slice().sort(byName)[0].id")
        await page.click(f'#invList .stk[data-id="{fid}"]'); await page.wait_for_timeout(200)
        c.ok(await ev("!!document.querySelector('.dlg input')"), 'Bestand-Fenster mit Eingabefeld')
        await page.fill('.dlg input', '7,5'); await page.click('.dlg [data-x=ok]'); await page.wait_for_timeout(300)
        c.eq(await ev("S.inventory.slice().sort(byName)[0].qty"), 7.5, 'Bestand mit Komma gesetzt')
        c.eq(await ev("S.inventory.slice().sort(byName)[0].moves.at(-1).kind"), 'fix', 'Korrektur steht im Verlauf')

        # Lager: kein +, „−“ entnimmt mit Rückgängig, Verlauf mit Zurücknehmen
        c.eq(await ev("$$('#invList [aria-label=mehr]').length"), 0, 'kein +-Knopf in der Lagerliste')
        iid = await ev("S.inventory.slice().sort(byName)[0].id")
        q0 = await ev(f"S.inventory.find(i=>i.id==='{iid}').qty")
        await page.click(f'#invList [data-a=invTake][data-id="{iid}"]'); await page.wait_for_timeout(300)
        c.ok(await ev(f"S.inventory.find(i=>i.id==='{iid}').qty") < q0, '„−“ verringert den Bestand')
        c.eq(await ev(f"S.inventory.find(i=>i.id==='{iid}').moves.at(-1).kind"), 'take', 'Entnahme im Verlauf')
        await page.click('#toast .tbtn'); await page.wait_for_timeout(300)
        c.eq(await ev(f"[S.inventory.find(i=>i.id==='{iid}').qty,S.inventory.find(i=>i.id==='{iid}').moves.some(m=>m.kind==='take')]"), [q0, False], 'Rückgängig im Hinweis stellt Bestand her')
        await page.click(f'#invList [data-a=invTake][data-id="{iid}"]'); await page.wait_for_timeout(300)
        await ev(f"(()=>{{const e=S.entries.find(e=>e.carId==='{cid}');(e.parts=e.parts||[]).push({{name:'Test',invId:'{iid}',qty:1}});return 1}})()")
        await page.click('[data-a=invLog]'); await page.wait_for_timeout(300)
        c.ok(await ev("$$('#invLogList .item').length") > 0, 'Lager-Verlauf zeigt Bewegungen')
        c.ok('Verbraucht' in await ev("$('#invLogList').textContent"), 'Verlauf zeigt Verbrauch aus Einträgen')
        await page.click('#invLogList [data-a=invMoveUndo]'); await page.wait_for_timeout(200)
        await page.click('.dlg [data-x=ok]'); await page.wait_for_timeout(400)
        c.eq(await ev(f"S.inventory.find(i=>i.id==='{iid}').qty"), q0, 'Entnahme im Verlauf zurückgenommen')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)

        # Regalböden nach Lagerort, Rolltor klappt ein und bleibt zu
        await H.go(page, '#/inv')
        locs = await ev("[...new Set(S.inventory.map(i=>(i.location||'').trim()||INV_NOLOC))].length")
        c.eq(await ev("$$('#invList .rack').length"), locs, 'ein Regalboden je Lagerort')
        await page.click('#invList .rack .rk-head'); await page.wait_for_timeout(600)
        loc = await ev("$('#invList .rack.shut')?.dataset.loc")
        c.ok(loc and await ev("$('#invList .rack.shut .rk-body').offsetHeight===0"), 'Rolltor zu: Boden eingeklappt')
        await page.reload(); await H.ready(page); await H.go(page, '#/inv')
        c.eq(await ev("$('#invList .rack.shut')?.dataset.loc"), loc, 'eingeklappt bleibt nach Neustart')
        await page.click('#invList .rack.shut .door'); await page.wait_for_timeout(600)
        c.eq(await ev("$$('#invList .rack.shut').length"), 0, 'Tippen aufs Rolltor öffnet wieder')

        # Zurück-Taste schließt nur das Fenster (Dialog), nicht das Werkzeug-Fenster darunter
        tid = await ev("S.tools.find(t=>!t.lentTo).id")
        await ev(f"toolView('{tid}')"); await page.wait_for_timeout(200)
        await page.click('#sheet .sheet-foot .btn:not(.primary)'); await page.wait_for_timeout(200)
        c.ok(await ev("!!document.querySelector('.dlg')"), 'Verleihen fragt im eigenen Fenster')
        await page.go_back(timeout=3000, wait_until='commit'); await page.wait_for_timeout(300)
        c.eq((await ev("!!document.querySelector('.dlg')"), await ev("sheetOpen")), (False, True), 'Zurück schließt nur das Frage-Fenster')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)

        # Archivieren ohne Rückfrage, mit Rückgängig
        bmw = await ev("myCars()[1].id")
        await ev(f"A.carArchive({{car:'{bmw}'}})"); await page.wait_for_timeout(300)
        c.eq(await ev(f"car('{bmw}').archived"), True, 'Auto ins Archiv ohne Rückfrage')
        await page.click('#toast .tbtn'); await page.wait_for_timeout(300)
        c.eq(await ev(f"car('{bmw}').archived"), False, 'Archivieren rückgängig')

        # Standardwerte: Zubehör übernimmt Akku-System & Marke, Parkside → 3 Jahre Garantie
        await ev("(async()=>{const t=S.tools[0];t.system='Parkside Performance 20 V';t.brand='Parkside Performance';t.purchaseDate='2026-01-01';await put('tools',t)})()")
        await ev("toolForm(null,'acc')"); await page.wait_for_timeout(200)
        f = await ev("(()=>{const f=$('#fTool');return[f.elements.namedItem('system').value,f.elements.namedItem('brand').value,f.elements.namedItem('warrantyUntil').value]})()")
        c.eq(f[:2], ['Parkside Performance 20 V', 'Parkside Performance'], 'neues Zubehör: Akku-System und Marke vorbelegt')
        c.eq(f[2], await ev("addMonths(today(),36)"), 'Parkside: Garantie 3 Jahre vorbelegt')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)
        await ev("toolForm()"); await page.wait_for_timeout(200)
        await page.fill('#fTool [name=brand]', 'Parkside'); await page.press('#fTool [name=brand]', 'Tab'); await page.wait_for_timeout(200)
        c.eq(await ev("$('#fTool [name=warrantyUntil]').value"), await ev("addMonths(today(),36)"), 'Marke Parkside eingetippt → 3 Jahre Garantie')
        c.ok(await ev("getComputedStyle($('#toolPhCtl [data-a=toolPhotoCrop]')).display==='none'"), 'ohne Foto keine Zuschnitt-Knöpfe')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)

        # Eintrag-Formular: einklappbare Abschnitte mit Zusammenfassung, Werkstatt-Feld nur bei „Werkstatt“
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        c.eq(await ev("$$('#fEntry details.fsec[open]').length"), 0, 'neuer Eintrag: Abschnitte eingeklappt')
        c.eq(await ev("$('#sum-parts').textContent"), 'keine', 'Zusammenfassung Teile: keine')
        c.ok(await ev("$('#fEntry .ws-only').hidden"), 'Werkstatt-Feld bei „selbst“ ausgeblendet')
        await page.click('#fEntry .seg label:nth-child(2)'); await page.wait_for_timeout(100)
        c.ok(not await ev("$('#fEntry .ws-only').hidden"), 'Werkstatt-Feld bei „Werkstatt“ sichtbar')
        await page.fill('#fEntry [name=title]', 'Ölwechsel'); await page.dispatch_event('#fEntry [name=title]', 'change'); await page.wait_for_timeout(200)
        c.ok('Motoröl' in await ev("$('#sum-iv').textContent"), 'automatisch angehaktes Intervall steht in der Zusammenfassung')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)
        oil = await ev(f"S.entries.find(e=>e.carId==='{cid}'&&e.category==='Ölwechsel').id")
        await ev(f"entryForm({{copyOf:'{oil}'}})"); await page.wait_for_timeout(200)
        c.ok(await ev("$('#sec-parts').open") and '3 Teile' in await ev("$('#sum-parts').textContent"), 'kopierter Eintrag: Teile offen, „3 Teile“')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)
        # Neu-Menü: Tanken zuerst
        await ev("quick()"); await page.wait_for_timeout(200)
        c.eq(await ev("$('#sheet .qbig .qbtn').textContent.trim()"), 'Tanken', 'Neu-Menü beginnt mit Tanken')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)

        # Backup teilen: wird beim Öffnen der Seite vorbereitet, Tippen teilt sofort (Chrome braucht frischen Fingertipp)
        await ev("navigator.canShare=()=>true;window._shared=0;navigator.share=async()=>{if(!navigator.userActivation.isActive)throw new DOMException('x','NotAllowedError');window._shared++};1")
        await H.go(page, '#/backup'); await page.wait_for_timeout(1500)
        await page.click('[data-a=shareBackup]'); await page.wait_for_timeout(500)
        c.eq(await ev("window._shared"), 1, 'Backup teilen klappt mit einem Tipp')

        # runder +-Knopf nicht auf Werkstatt/Lager
        await H.go(page, '#/tools')
        c.ok(await ev("getComputedStyle($('.fab')).display==='none'"), 'kein +-Knopf auf Werkstatt')
        await H.go(page, '#/home')
        c.ok(await ev("getComputedStyle($('.fab')).display!=='none'"), '+-Knopf auf Start')

        # Tippflächen auf den wichtigsten Seiten
        small = []
        for h in ['#/home', f'#/car/{cid}', f'#/car/{cid}/iv', '#/tools', '#/inv', '#/shop', '#/todos', '#/stats', '#/settings']:
            await H.go(page, h)
            small += [dict(x, page=h) for x in await ev(SMALL)]
        await ev(f"entryForm({{carId:'{cid}'}})"); await page.wait_for_timeout(200)
        small += [dict(x, page='entryForm') for x in await ev(SMALL)]
        await ev("closeSheet(false,true)")
        for x in small[:12]:
            print('   klein:', x)
        c.eq(len(small), 0, 'alle Knöpfe mindestens 40 px')
        c.eq(page.errors, [], 'keine JS-Fehler')
        await b.close()

        # leere Datenbank: Willkommen mit Schritten
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base, empty=True)
        t = await page.evaluate("$('#view').textContent")
        c.ok('Willkommen' in t and 'Erstes Auto anlegen' in t, 'leere App: Willkommen mit nächsten Schritten')
        await H.go(page, '#/stats')
        c.ok('Noch keine Daten' in await page.evaluate("$('#view').textContent"), 'leere Statistik erklärt, was kommt')
        await b.close()
    return c.done()

if __name__ == '__main__':
    H.run(main)

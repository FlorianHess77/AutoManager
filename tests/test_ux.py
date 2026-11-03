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
        c.eq(await ev("[...$$('#sheet .qbig .qbtn')].map(b=>b.textContent.trim())"), ['Wartung / Reparatur', 'Tanken', 'To-do', 'km-Stand'], 'Neu-Menü: Wartung, Tanken, To-do, km-Stand')
        c.ok(await ev("!!$('#sheet [data-file=quickPump]')&&!!$('#sheet [data-file=quickOdo]')&&!$('#sheet [data-a=pkDone]')"), 'Neu-Menü: Foto-Knöpfe Zapfsäule und km-Stand, ohne Pickerl/Beleg')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)

        # Backup teilen: wird beim Öffnen der Seite vorbereitet, Tippen teilt sofort (Chrome braucht frischen Fingertipp)
        await ev("navigator.canShare=()=>true;window._shared=0;navigator.share=async()=>{if(!navigator.userActivation.isActive)throw new DOMException('x','NotAllowedError');window._shared++};1")
        await H.go(page, '#/backup'); await page.wait_for_timeout(1500)
        await page.click('[data-a=shareBackup]'); await page.wait_for_timeout(500)
        c.eq(await ev("window._shared"), 1, 'Backup teilen klappt mit einem Tipp')

        # Werkstatt als Raum: Tab führt in den Raum, Antippen zoomt in den Bereich, Zurück in den Raum
        await page.click('#tabs [data-nk=tools]'); await page.wait_for_timeout(600)
        c.eq(await ev("location.hash"), '#/ws', 'Werkstatt-Tab öffnet den Raum')
        c.eq(await ev("$$('#wsRoom [data-a=wsGo]').length"), 6, 'Raum: 6 antippbare Dinge')
        c.ok(await ev("document.documentElement.scrollHeight<=innerHeight+1"), 'Raum füllt den Bildschirm ohne Scrollen')
        await page.tap('#ws-tools'); await page.wait_for_timeout(900)
        c.eq((await ev("location.hash"), await ev("!$('#backBtn').hidden")), ('#/tools', True), 'Werkzeugwagen → Werkzeug, mit Zurück-Pfeil')
        await page.go_back(); await page.wait_for_timeout(700)
        c.eq(await ev("location.hash"), '#/ws', 'Android-Zurück → wieder im Raum')
        await page.tap('#ws-inv'); await page.wait_for_timeout(900)
        c.eq(await ev("location.hash"), '#/inv', 'Regal → Teilelager')
        await page.click('#tabs [data-nk=tools]'); await page.wait_for_timeout(700)
        await page.tap('#ws-shop'); await page.wait_for_timeout(900)
        c.eq((await ev("location.hash"), await ev("$('#backBtn').dataset.h")), ('#/shop', '#/ws'), 'Zettel → Einkaufsliste, zurück in den Raum')
        await page.click('#backBtn'); await page.wait_for_timeout(700)
        await page.tap('#ws-log'); await page.wait_for_timeout(500)
        c.ok(await ev("sheetOpen&&!!$('#invLogList')"), 'Lagerbuch → Lager-Verlauf')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)
        await page.tap('#ws-clock'); await page.wait_for_timeout(900)
        c.eq(await ev("location.hash"), '#/calendar', 'Uhr → Kalender')
        # abschaltbar in den Einstellungen
        await H.go(page, '#/settings')
        await page.click('[data-change=wsRoom]'); await page.wait_for_timeout(300)
        c.eq(await ev("localStorage.getItem('garage.wsRoom')"), '0', 'Schalter speichert „aus“')
        await page.click('#tabs [data-nk=tools]'); await page.wait_for_timeout(500)
        c.eq((await ev("location.hash"), await ev("$('#backBtn').hidden")), ('#/tools', True), 'Raum aus: Tab öffnet gleich die Werkzeugliste')
        await H.go(page, '#/settings'); await page.click('[data-change=wsRoom]'); await page.wait_for_timeout(300)
        c.eq(await ev("$('#tabs [data-nk=tools]').dataset.h"), '#/ws', 'Raum wieder an')

        # Batterie: Spannung eintragen, Chronik, Meilenstein-Hinweis
        await H.go(page, f'#/car/{cid}')
        await page.click('#view [data-a=batOpen]'); await page.wait_for_timeout(300)
        await page.click('#sheet [data-a=batMeasure]'); await page.wait_for_timeout(200)
        await page.fill('.dlg input', '12,48'); await page.click('.dlg [data-x=ok]'); await page.wait_for_timeout(400)
        c.eq(await ev(f"car('{cid}').battery.checks.at(-1).volt"), 12.48, 'Batterie: Spannung mit Komma gespeichert')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(200)
        await page.click('#view [data-h^="#/chronik/"]'); await page.wait_for_timeout(400)
        c.ok(await ev("location.hash.startsWith('#/chronik/')&&$$('#view .ch-ev').length>=3&&!!$('#view .ch-year')"), 'Chronik: Zeitleiste mit Jahren')
        n0 = await ev("$$('#view .ch-ev').length")
        await page.click('#view .seg label:nth-child(2)'); await page.wait_for_timeout(300)
        c.ok(await ev("$$('#view .ch-ev').length") > n0, 'Chronik „Alles“ zeigt mehr Einträge')
        await ev("chronAll=false;1")

        # km-Stand vom Tacho-Foto (Texterkennung nachgestellt): plausibelste Zahl, Foto wird nicht gespeichert
        ph0 = await ev("allPhotos().then(a=>a.length)")
        last = await ev(f"carOdo('{cid}')")
        await ev(f"""window._ocrText='20 40 60\\n{last + 432}\\nTRIP 1234\\n15 07';ocrWorkerGet=async()=>({{setParameters:async()=>{{}},recognize:async()=>({{data:{{text:window._ocrText}}}})}});odoForm('{cid}');1""")
        await page.wait_for_timeout(200)
        await page.set_input_files('#sheet [data-file=odoPhoto]', os.path.join(os.path.dirname(__file__), '..', 'icon-512.png')); await page.wait_for_timeout(800)
        c.eq(await ev("num($('#fOdo [name=odo]').value)"), last + 432, 'Tacho-Foto: km-Stand erkannt (Skala, Tageskilometer, Uhr ignoriert)')
        c.ok('Gelesen' in await ev("$('#ocrState').textContent") and '+432 km' in await ev("$('#odoPlaus').textContent"), 'Hinweis mit Plausibilität (+432 km seit …)')
        await ev(f"window._ocrText='{last - 5000}\\n12';1")
        await page.set_input_files('#sheet [data-file=odoPhoto]', os.path.join(os.path.dirname(__file__), '..', 'icon-512.png')); await page.wait_for_timeout(800)
        c.ok('Kein passender' in await ev("$('#ocrState').textContent") and await ev("!!$('#ocrState [data-a=odoCrop]')"), 'unplausible Zahl wird nicht übernommen, Angebot zum Markieren')
        await page.fill('#fOdo [name=odo]', str(last + 90000)); await page.click('#sheet .sheet-foot .btn.primary'); await page.wait_for_timeout(300)
        c.ok(await ev("!!document.querySelector('.dlg')"), 'unrealistisch hoher km-Stand: Rückfrage vor dem Speichern')
        await page.click('.dlg [data-x=no]'); await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)
        c.eq(await ev("allPhotos().then(a=>a.length)"), ph0, 'Tacho-Foto wird nicht gespeichert')

        # Tanken per Foto: Zapfsäule (Betrag = Liter × Literpreis) und danach Tacho
        img = os.path.join(os.path.dirname(__file__), '..', 'icon-512.png')
        last = await ev(f"carOdo('{cid}')")
        await ev(f"window._ocrText='95 4\\n6543\\n3852\\n1699';fuelForm(null,'{cid}');1"); await page.wait_for_timeout(200)
        await page.set_input_files('#sheet [data-file=fuelPump]', img); await page.wait_for_timeout(800)
        r = await ev("['liters','ppl','price'].map(n=>num($('#fFuel [name='+n+']').value))")
        c.eq(r, [38.52, 1.699, 65.43], 'Zapfsäule ohne Kommas: Liter, €/l, Betrag richtig zugeordnet')
        c.ok(await ev("!!$('#ocrState [data-file=fuelOdo]')"), 'danach Knopf „Jetzt Tacho fotografieren“')
        await ev(f"window._ocrText='120 140\\n{last + 610}\\n3852';1")
        await page.set_input_files('#ocrState [data-file=fuelOdo]', img); await page.wait_for_timeout(800)
        c.eq(await ev("num($('#fFuel [name=odo]').value)"), last + 610, 'Tacho nach der Zapfsäule: km-Stand übernommen')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)
        await ev("window._ocrText='12 34 56';fuelForm(null,'"+cid+"');1"); await page.wait_for_timeout(200)
        await page.set_input_files('#sheet [data-file=fuelPump]', img); await page.wait_for_timeout(800)
        c.ok(await ev("!$('#fFuel [name=liters]').value&&$('#ocrState').textContent.includes('passten nicht')"), 'Zapfsäule: nicht zusammenpassende Werte werden nicht übernommen')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)

        # Neu-Menü: ein Tipp → Zapfsäulen-Foto bzw. km-Stand-Foto
        img = os.path.join(os.path.dirname(__file__), '..', 'icon-512.png')
        await H.go(page, f'#/car/{cid}')
        await ev("window._ocrText='6543\\n3852\\n1699';quick();1"); await page.wait_for_timeout(200)
        await page.set_input_files('#sheet [data-file=quickPump]', img); await page.wait_for_timeout(900)
        c.ok(await ev("!!$('#fFuel')&&num($('#fFuel [name=price]').value)===65.43&&$('#fFuel [name=carId]').value===%r" % cid), 'Neu › Zapfsäule-Foto: Tankung mit Werten, richtiges Auto')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)
        last = await ev(f"carOdo('{cid}')")
        await ev(f"window._ocrText='{last + 77}';quick();1"); await page.wait_for_timeout(200)
        await page.set_input_files('#sheet [data-file=quickOdo]', img); await page.wait_for_timeout(900)
        c.eq(await ev("$('#fOdo')&&num($('#fOdo [name=odo]').value)"), last + 77, 'Neu › km-Stand-Foto: km-Stand-Fenster mit gelesenem Wert')
        await ev("closeSheet(false,true)"); await page.wait_for_timeout(300)

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

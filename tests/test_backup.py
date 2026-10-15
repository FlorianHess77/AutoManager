"""Backup: Export → Import ergibt dieselben Daten; kaputte Datei darf nichts löschen.

python3 tests/test_backup.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

STATE = "JSON.stringify(Object.fromEntries(STORES.filter(s=>s!=='photos').map(s=>[s,S[s].slice().sort((a,b)=>a.id<b.id?-1:1)])))"
# Backup einlesen; die Rückfrage („Wiederherstellen“) wird automatisch bestätigt
IMPORT = """async(txt)=>{const p=importJSON([new File([txt],'b.json',{type:'application/json'})]);
 for(let i=0;i<30;i++){const ok=document.querySelector('.dlg [data-x=ok]');if(ok){ok.click();break}await new Promise(r=>setTimeout(r,50))}
 await p;await new Promise(r=>setTimeout(r,300))}"""
DBCOUNT = """async()=>{const d=await openDB();const out={};for(const s of STORES){out[s]=await reqP(d.transaction(s).objectStore(s).count())}d.close();return out}"""


async def main():
    c = H.Check('Backup')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base)
        ev = page.evaluate
        # ein Foto dazu
        await ev("put('photos',{id:'p1',data:'data:image/jpeg;base64,AAAA'})")
        before = await ev(STATE)
        bj = await ev("backupJSON()")
        d = json.loads(bj)
        c.eq(d['app'], 'garage-wartung', 'Backup-Kennung')
        c.ok(any(x['id'] == 'p1' for x in d['photos']), 'Foto im Backup')
        # Rundreise
        await ev("clearAll()")
        await ev(IMPORT, bj)
        c.eq(await ev(STATE), before, 'Import stellt alle Daten wieder her')
        c.eq(await ev("getPhoto('p1')"), 'data:image/jpeg;base64,AAAA', 'Foto wiederhergestellt')
        cnt = await ev(DBCOUNT)
        c.eq(cnt['entries'], len(d['data']['entries']), 'Einträge auch in der Datenbank')

        # Kaputtes Backup (ein Eintrag ohne id) → nichts darf verloren gehen
        bad = json.loads(bj)
        bad['data']['entries'].append({'title': 'kaputt ohne id', 'date': '2026-01-01'})
        await ev(IMPORT, json.dumps(bad))
        c.eq(await ev(STATE), before, 'Kaputtes Backup: aktuelle Daten bleiben erhalten (Speicher)')
        cnt2 = await ev(DBCOUNT)
        c.eq(cnt2['entries'], len(d['data']['entries']), 'Kaputtes Backup: Datenbank unverändert')
        c.ok(cnt2['photos'] >= 1, 'Kaputtes Backup: Fotos noch da')

        # Keine JSON-Datei
        await ev(IMPORT, 'das ist kein backup')
        c.eq(await ev(STATE), before, 'Falsche Datei: Daten bleiben')

        # nach Neuladen alles noch da
        await page.reload(); await H.ready(page)
        c.eq(await ev(STATE), before, 'nach Neuladen identisch')
        await b.close()
    return c.done()

if __name__ == '__main__':
    H.run(main)

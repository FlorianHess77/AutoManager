"""Klickt alle Seiten und die wichtigsten Fenster durch und macht Screenshots.

python3 tests/crawl.py [dark|light] [breite] [demo|empty]
Ergebnis: tests/_shots/<modus>/*.png und eine Liste der JS-Fehler.
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

PAGES = ['#/home', '#/cars', '#/todos', '#/ws', '#/tools', '#/inv', '#/shop', '#/search', '#/calendar', '#/stats',
         '#/prices', '#/warranty', '#/archive', '#/backup', '#/settings', '#/help', '#/more']
CAR_TABS = ['ov', 'hist', 'fuel', 'odo', 'iv', 'tyre', 'issue', 'tech', 'guide', 'docs']


async def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else 'dark'
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 390
    mode = sys.argv[3] if len(sys.argv) > 3 else 'demo'
    tag = f'{mode}-{theme}-{width}'
    H.OUT = os.path.join(H.OUT, tag)
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base, width=width, height=844 if width < 700 else 900, theme=theme, empty=(mode == 'empty'))
        n = 0
        for h in PAGES:
            await H.go(page, h)
            await H.shot(page, f'{n:02d}-{h[2:].replace("/", "_") or "home"}'); n += 1
        # Verlauf-Reiter auf der Startseite
        await H.go(page, '#/home')
        await page.evaluate("A.homeTab({t:'log'})"); await page.wait_for_timeout(300)
        await H.shot(page, f'{n:02d}-home-log'); n += 1
        await page.evaluate("A.homeTab({t:'ov'})")
        cars = await page.evaluate("S.cars.map(c=>({id:c.id,n:dispName(c),a:!!c.archived,f:!!c.foreign}))")
        for c in cars[:3]:
            for t in CAR_TABS:
                await H.go(page, f'#/car/{c["id"]}/{t}')
                await H.shot(page, f'{n:02d}-car-{c["n"].replace(" ", "")}-{t}'); n += 1
        # Fenster
        cid = cars[0]['id'] if cars else ''
        sheets = [
            ('quick', "quick()"),
            ('entryForm', f"entryForm({{carId:'{cid}'}})"),
            ('pkForm', f"pkForm({{carId:'{cid}'}})"),
            ('fuelForm', f"fuelForm(null,'{cid}')"),
            ('carForm', f"carForm('{cid}')"),
            ('carFormNew', "carForm()"),
            ('todoForm', "todoForm()"),
            ('toolForm', "toolForm()"),
            ('accForm', "toolForm(null,'acc')"),
            ('invForm', "invForm()"),
            ('ivTpl', f"ivTplSheet('{cid}')"),
            ('ivForm', f"ivForm('{cid}')"),
            ('tyreForm', f"tyreForm('{cid}')"),
            ('issueForm', f"issueForm('{cid}')"),
            ('guideForm', f"guideForm('{cid}')"),
            ('odoForm', f"odoForm('{cid}')"),
            ('carMenu', f"carMenu('{cid}')"),
            ('sellForm', f"sellForm('{cid}')"),
            ('exposeForm', f"exposeForm('{cid}')"),
            ('qrSheet', f"qrSheet('{cid}')"),
            ('pkOpen', f"pkOpen('{cid}')"),
            ('dlNew', f"dlNew('{cid}')"),
            ('torque', f"torqueSheet('{cid}')"),
            ('rate', "rateForm()"),
            ('wrapped', "wrappedSheet('2026')"),
            ('carDoc', f"carDocForm('{cid}')"),
        ]
        for name, js in sheets:
            if not cid and name not in ('quick', 'carFormNew', 'todoForm', 'toolForm', 'accForm', 'invForm', 'rate', 'wrapped'):
                continue
            await H.go(page, '#/home')
            try:
                await page.evaluate(js)
                await page.wait_for_timeout(300)
                await H.sheet_shot(page, f'{n:02d}-sheet-{name}'); n += 1
            except Exception as e:
                print('Fenster', name, 'Fehler:', e)
            await page.evaluate("sheetOpen&&closeSheet()")
            await page.wait_for_timeout(150)
        # erstes Werkzeug / Eintrag ansehen
        for name, js in [('toolView', "S.tools[0]&&toolView(S.tools[0].id)"), ('entryView', "S.entries.find(e=>e.category!=='Pickerl')&&entryView(S.entries.find(e=>e.category!=='Pickerl').id)"),
                         ('pkView', "S.entries.find(e=>e.category==='Pickerl')&&pkView(S.entries.find(e=>e.category==='Pickerl').id)"),
                         ('ivOpen', "S.intervals[0]&&ivOpen(S.intervals[0].id)"), ('guideView', "S.guides[0]&&guideView(S.guides[0].id)")]:
            await H.go(page, '#/home')
            await page.evaluate(js); await page.wait_for_timeout(300)
            if await page.evaluate("sheetOpen"):
                await H.sheet_shot(page, f'{n:02d}-sheet-{name}'); n += 1
                await page.evaluate("closeSheet()")
        await b.close()
    errs = sorted(set(page.errors))
    print(f'{tag}: {n} Screenshots in {H.OUT}')
    print('JS-Fehler:', len(errs))
    for e in errs:
        print('  ', e[:300])
    return not errs

if __name__ == '__main__':
    H.run(main)

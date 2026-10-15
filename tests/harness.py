"""Gemeinsame Hilfen für die Playwright-Tests der Garagen-App.

Startet einen lokalen Webserver auf dem Repo-Ordner und öffnet die App in
Chromium (390×844, Touch, de-AT). Aufruf der Tests:  python3 tests/<datei>.py
"""
import asyncio, os, threading, http.server, socketserver, functools, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('SHOTS', os.path.join(ROOT, 'tests', '_shots'))


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        # wie GitHub Pages: kurz cachen, damit Update-Verhalten realistisch bleibt
        self.send_header('Cache-Control', 'max-age=600')
        super().end_headers()


def serve():
    """Startet einen Server im Hintergrund und gibt die Basis-URL zurück."""
    handler = functools.partial(_Quiet, directory=ROOT)
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/', srv


async def open_app(browser, base, width=390, height=844, theme=None, empty=False,
                   sw=False, hash_='', init=''):
    """Neuer Kontext (= frische IndexedDB) mit der App.

    empty=True  → keine Beispieldaten (wie nach „Alle Daten löschen“)
    theme       → 'dark' | 'light' | 'system'
    """
    ctx = await browser.new_context(
        viewport={'width': width, 'height': height}, device_scale_factor=1,
        has_touch=True, is_mobile=True, locale='de-AT', timezone_id='Europe/Vienna',
        service_workers='allow' if sw else 'block')
    js = ''
    if empty:
        js += "localStorage.setItem('garage.seeded','1');"
    if theme:
        js += f"localStorage.setItem('garage.theme','{theme}');"
    js += "localStorage.setItem('garage.installHide','1');" + init
    if js:
        await ctx.add_init_script(f"try{{if(!sessionStorage.getItem('t.init')){{{js}sessionStorage.setItem('t.init','1')}}}}catch(e){{}}")
    page = await ctx.new_page()
    page.errors = []
    page.on('pageerror', lambda e: page.errors.append('pageerror: ' + str(e)))
    page.on('console', lambda m: page.errors.append('console: ' + m.text) if m.type == 'error' else None)
    page.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await page.goto(base + 'index.html' + hash_)
    await ready(page)
    return ctx, page


async def ready(page):
    await page.wait_for_function("document.querySelector('#view') && document.querySelector('#view').children.length>0")
    await page.wait_for_timeout(250)


async def go(page, h):
    await page.evaluate(f"(()=>{{if(typeof sheetOpen!=='undefined'&&sheetOpen)closeSheet();location.hash={h!r}}})()")
    await page.wait_for_timeout(350)


async def shot(page, name, full=True):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + '.png')
    await page.screenshot(path=p, full_page=full)
    return p


async def sheet_shot(page, name):
    """Screenshot eines offenen Fensters inkl. gescrolltem Inhalt (ganzer Panel-Inhalt)."""
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + '.png')
    h = await page.evaluate("(()=>{const p=document.querySelector('#sheet .sheet-panel');return p?p.scrollHeight:0})()")
    vp = page.viewport_size
    if h and h > vp['height']:
        await page.set_viewport_size({'width': vp['width'], 'height': min(int(h) + 80, 6000)})
        await page.wait_for_timeout(150)
        await page.screenshot(path=p)
        await page.set_viewport_size(vp)
    else:
        await page.screenshot(path=p)
    return p


class Check:
    """Kleine Assertion-Sammlung mit lesbarer Ausgabe."""

    def __init__(self, name):
        self.name, self.fails, self.n = name, [], 0

    def ok(self, cond, msg):
        self.n += 1
        if not cond:
            self.fails.append(msg)
            print('  ✗', msg)

    def eq(self, a, b, msg):
        cut = lambda v: (repr(v)[:160] + ' …') if len(repr(v)) > 160 else repr(v)
        self.ok(a == b, f'{msg}: erwartet {cut(b)}, ist {cut(a)}')

    def near(self, a, b, msg, tol=0.01):
        self.ok(a is not None and abs(a - b) <= tol, f'{msg}: erwartet ≈{b!r}, ist {a!r}')

    def done(self):
        print(f'{self.name}: {self.n - len(self.fails)}/{self.n} ok')
        return not self.fails


def run(main):
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)

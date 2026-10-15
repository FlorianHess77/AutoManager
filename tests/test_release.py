"""Release-Check: Version in sw.js und index.html stimmen überein, Dateien vorhanden.

python3 tests/test_release.py
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import harness as H


def main():
    c = H.Check('Release')
    sw = open(os.path.join(H.ROOT, 'sw.js'), encoding='utf-8').read()
    html = open(os.path.join(H.ROOT, 'index.html'), encoding='utf-8').read()
    app = re.search(r"const APP_VER='garage-v(\d+)'", html)
    c.ok(app, 'APP_VER in index.html gefunden')
    c.ok("searchParams.get('v')" in sw and 'garage-v' not in sw, 'sw.js übernimmt die Version aus index.html (keine eigene Nummer)')
    c.ok("register('sw.js?v='" in html, 'Service Worker wird mit Version registriert')
    for f in re.findall(r"'\./([^']*)'", sw.split('FILES=')[1].split(';')[0]):
        if f:
            c.ok(os.path.exists(os.path.join(H.ROOT, f)), f'Datei für Offline-Cache vorhanden: {f}')
    m = json.load(open(os.path.join(H.ROOT, 'manifest.webmanifest'), encoding='utf-8'))
    for i in m['icons']:
        c.ok(os.path.exists(os.path.join(H.ROOT, i['src'])), f"Icon vorhanden: {i['src']}")
    c.ok('interactive-widget=resizes-content' in html, 'Tastatur verkleinert die Seite (viewport)')
    return c.done()


if __name__ == '__main__':
    sys.exit(0 if main() else 1)

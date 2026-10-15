#!/bin/sh
# Alle Tests der Garagen-App. Aufruf im Repo-Ordner:  sh tests/run_all.sh
# Braucht Python 3 mit Playwright (Chromium). Screenshots: tests/_shots/ (nicht im Git).
cd "$(dirname "$0")/.." || exit 1
fail=0
for t in test_release test_logic test_nav test_backup test_robust test_ux test_perf; do
  echo "== $t"
  python3 "tests/$t.py" || fail=1
done
echo "== crawl (alle Seiten, dunkel 390 / hell 360 / leer)"
python3 tests/crawl.py dark 390 demo | tail -2 || fail=1
python3 tests/crawl.py light 360 demo | tail -2 || fail=1
python3 tests/crawl.py dark 390 empty | tail -2 || fail=1
[ $fail = 0 ] && echo "ALLES OK" || echo "FEHLER – siehe oben"
exit $fail

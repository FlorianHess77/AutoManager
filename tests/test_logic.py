"""Rechen-Logik mit Grenzfällen (läuft im Browser gegen die echte App).

python3 tests/test_logic.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

# Hilfsfunktionen im Browser: leere DB, Daten direkt anlegen
SETUP = r"""
window.T={
 async reset(){await clearAll()},
 car(o){const c={id:uid(),name:'Testauto',make:'Test',model:'',fuel:'Benzin',firstReg:'2000-03-15',deadlines:[],specs:[],archived:false,created:'2020-01-01',...o};return put('cars',c).then(()=>c)},
 entry(o){const e={id:uid(),date:'2026-01-01',odo:null,category:'Wartung',title:'x',desc:'',diy:true,workshop:'',hours:null,labor:null,notes:'',parts:[],photos:[],intervalIds:[],toolIds:[],...o};return put('entries',e).then(()=>e)},
 fuel(o){const f={id:uid(),date:'2026-01-01',odo:null,liters:40,price:60,ppl:1.5,type:'Super 95',station:'',full:true,note:'',...o};return put('fuel',f).then(()=>f)},
 iv(o){const v={id:uid(),name:'Öl',km:15000,months:12,warnKm:1000,warnDays:30,match:'',category:'',...o};return put('intervals',v).then(()=>v)},
 tool(o){const t={id:uid(),name:'Werkzeug',category:'Handwerkzeug',extraUses:0,...o};return put('tools',t).then(()=>t)},
};
"""


async def main():
    c = H.Check('Logik')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base, empty=True)
        await page.evaluate(SETUP)
        ev = page.evaluate

        # ---------- Zahlen mit Komma ----------
        for s, want in [('1.234,5', 1234.5), ('12,5', 12.5), ('12.5', 12.5), ('1.500', 1500), ('248 480', 248480),
                        ('€ 12,90', 12.9), ('', None), ('abc', None), ('-3,5', -3.5), ('0', 0)]:
            c.eq(await ev(f"num({s!r})"), want, f'num({s!r})')

        # ---------- Strings statt Zahlen (z. B. aus altem/handbearbeitetem Backup) ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({purchase:'2024-01-01',purchasePrice:'1000',purchaseOdo:'100000'});
          await T.entry({carId:c.id,date:'2025-01-01',odo:'110000',parts:[{name:'a',price:'10.5'},{name:'b',price:'4,5'}],labor:'20',hours:'2',diy:true});
          await T.fuel({carId:c.id,date:'2025-02-01',odo:'111000',liters:'40',price:'60',full:true});
          await T.fuel({carId:c.id,date:'2025-03-01',odo:'111500',liters:'30',price:'45',full:true});
          typeof normalizeAll==='function'&&normalizeAll();
          const oc=ownCost(c);return{odo:carOdo(c.id),cost:entryCost(S.entries[0]),fc:fuelCalc(c.id).avg,total:oc.total,km:oc.kmDriven}})()""")
        c.eq(r['odo'], 111500, 'km-Stand mit Strings')
        c.eq(r['cost'], 35, 'Eintragskosten mit Strings (10,5+4,5+20)')
        c.near(r['fc'], 6.0, 'Verbrauch mit Strings')
        c.eq(r['km'], 11500, 'km seit Kauf mit Strings')

        # ---------- Verbrauch: Teil-Tankung ohne km ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});
          await T.fuel({carId:c.id,date:'2026-01-01',odo:1000,liters:40,full:true});
          await T.fuel({carId:c.id,date:'2026-01-10',odo:null,liters:10,full:false});
          await T.fuel({carId:c.id,date:'2026-01-20',odo:1500,liters:20,full:true});
          return fuelCalc(c.id).avg})()""")
        c.near(r, 6.0, 'Verbrauch: Teil-Tankung ohne km wird mitgezählt (30 l / 500 km)')

        # ---------- Verbrauch: eine einzige Tankung ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});await T.fuel({carId:c.id,odo:1000});const f=fuelCalc(c.id);return [f.avg,f.cost,f.liters]})()""")
        c.eq(r, [None, 60, 40], 'eine Tankung: kein Ø, Kosten und Liter stimmen')

        # ---------- Tankung nur mit Literpreis → Betrag wird ergänzt ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});fuelForm(null,c.id);const f=$('#fFuel');
          f.elements.namedItem('odo').value='1000';f.elements.namedItem('ppl').value='1,659';f.elements.namedItem('ppl').dispatchEvent(new Event('input',{bubbles:true}));
          f.elements.namedItem('liters').value='40';f.elements.namedItem('liters').dispatchEvent(new Event('input',{bubbles:true}));
          await saveFuel(f);return S.fuel[0]?.price})()""")
        c.near(r, 66.36, 'Tankung: Betrag aus Liter × Literpreis')

        # ---------- Kosten & Bilanz: nur Besitzzeit ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({purchase:'2024-01-01',purchasePrice:1000,purchaseOdo:100000,insYear:600});
          await T.entry({carId:c.id,date:'2020-05-01',odo:80000,labor:500,diy:false,title:'Vorbesitzer'});
          await T.entry({carId:c.id,date:'2024-06-01',odo:105000,labor:100,diy:false});
          const o=ownCost(c);return{maint:o.maint,months:o.months}})()""")
        c.eq(r['maint'], 100, 'Kosten vor dem Kauf (Vorbesitzer) zählen nicht zur eigenen Bilanz')

        # ---------- Pickerl ----------
        await ev("T.reset()")
        async def pk(firstReg, last=None, today=None):
            js = f"""(async()=>{{const c=await T.car({{firstReg:{firstReg!r}}});
              {f"await T.entry({{carId:c.id,date:{last!r},category:'Pickerl',pk:{{result:'ok'}}}});" if last else ''}
              const p=pickerlStatus(c);return p&&{{label:p.label,ws:p.ws,we:p.we,st:p.st}}}})()"""
            if today:
                await page.clock.set_fixed_time(today)
            r = await ev(js)
            await ev("T.reset()")
            return r
        # alte Regel (bis Okt. 2027): -1/+4 Monate
        r = await pk('2000-03-15', '2026-03-20')
        c.eq((r['label'], r['ws'], r['we']), ('Pickerl 03/2027', '2027-02-01', '2027-07-31'), 'Audi: Pickerl 03/2027, Fenster alt')
        r = await pk('1996-11-05', '2025-11-12')
        c.eq((r['label'], r['ws'], r['we']), ('Pickerl 11/2026', '2026-10-01', '2027-03-31'), 'BMW: Pickerl 11/2026')
        # Übergang: Fälligkeit Aug–Okt 2027 → spätestens 30.11.2027
        r = await pk('2000-09-10', '2026-09-15')
        c.eq((r['label'], r['we']), ('Pickerl 09/2027', '2027-11-30'), 'Fällig 09/2027: Frist endet 30.11.2027 (Übergang)')
        # neue Regel ab Fälligkeit Nov. 2027: 4 Monate vorher bis Ende des Monats
        r = await pk('1996-11-05', '2026-11-20')
        c.eq((r['label'], r['ws'], r['we']), ('Pickerl 11/2027', '2027-07-01', '2027-11-30'), 'BMW 11/2027: neue Regel −4/0')
        r = await pk('2000-03-15', '2027-03-10')
        c.eq((r['label'], r['ws'], r['we']), ('Pickerl 03/2028', '2027-11-01', '2028-03-31'), 'Audi 03/2028: neue Regel')
        # früh gemacht (3 Monate vor Fälligkeit, neue Regel) zählt für diesen Termin
        r = await pk('2000-03-15', '2027-12-05')
        c.eq(r['label'], 'Pickerl 03/2029', 'Audi: Pickerl im Dez. 2027 (für 03/2028) → nächstes 03/2029')
        # Neuwagen nach neuer Regel 4-2-2-2-1
        r = await pk('2027-06-10')
        c.eq(r['label'], 'Pickerl 06/2031', 'Neuwagen EZ 06/2027: erstes Pickerl nach 4 Jahren')
        # Neuwagen alte Regel: 3 Jahre
        r = await pk('2024-04-02')
        c.eq(r['label'], 'Pickerl 04/2027', 'EZ 04/2024: erstes Pickerl 04/2027 (Plakette nach altem Recht)')
        r = await pk('2024-04-02', '2027-04-20')
        c.eq(r['label'], 'Pickerl 04/2029', 'EZ 04/2024, 1. Pickerl 04/2027 → +2 Jahre')
        r = await pk('2021-04-02', '2026-04-20')
        c.eq(r['label'], 'Pickerl 04/2027', 'EZ 04/2021: 2. Pickerl 2026 → 3. 2027 (alt)')
        r = await pk('2021-04-02', '2027-06-01')
        c.eq(r['label'], 'Pickerl 04/2029', 'EZ 04/2021: 3. Pickerl nach 19.5.2027 → +2 Jahre (neu)')
        await page.clock.set_fixed_time('2026-10-15T10:00:00')

        # ---------- Fremde Autos: nie in Abzeichen/Startseite ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const f=await T.car({foreign:true,name:'Freund',purchase:'2015-01-01',purchaseOdo:1000,odo:90000,
             docs:['Kaufvertrag','Zulassungsschein','Versicherung'].map(k=>({id:uid(),kind:k,type:'img'}))});
          await T.entry({carId:f.id,odo:90000});
          for(let i=0;i<10;i++)await T.fuel({carId:f.id,date:'2026-0'+(1+i%9)+'-01',photoId:'x'+i});
          const t=await T.entry({carId:f.id,title:'Bremse',category:'Bremsen'});
          const td={id:uid(),carId:f.id,title:'Fremd-To-do',prio:2,done:false,parts:[]};await put('todos',td);
          const got=earnedBadges();location.hash='#/home';render();
          return{got,home:$('#view').textContent.includes('Fremd-To-do')}})()""")
        for k in ['docs', 'km10k', 'km50k', 'loyal', 'rcpt', 'brake']:
            c.ok(k not in r['got'], f'Abzeichen „{k}“ darf nicht durch fremdes Auto kommen')
        c.ok('help' in r['got'], 'Abzeichen „Hilfsbereit“ kommt durch fremdes Auto (gewollt)')
        c.ok(not r['home'], 'To-do eines fremden Autos erscheint nicht auf der Startseite')

        # ---------- Werkzeug-Ersparnis ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const a=await T.tool({price:100,rentPrice:15,extraUses:3});const z=await T.tool({price:0,paid:0,rentPrice:10});
          return[toolCalc(a),toolCalc(z)]})()""")
        c.eq((r[0]['saved'], r[0]['amort'], r[0]['left']), (-55, False, 4), 'Werkzeug 100 €, 3× à 15 €: noch 55 € / 4 Einsätze')
        c.ok(not r[1]['amort'], 'Geschenktes Werkzeug ohne Einsatz ist nicht „amortisiert“')

        # ---------- Lagerwert ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{await put('inventory',{id:uid(),name:'Öl',qty:5,unit:'l',price:8.5});await put('inventory',{id:uid(),name:'Fett',qty:250,unit:'g',price:.048});
          await put('inventory',{id:uid(),name:'leer',qty:0,unit:'Stk',price:3});await put('inventory',{id:uid(),name:'ohne Preis',qty:2,unit:'Stk',price:null});
          location.hash='#/inv';render();return $('#view .card .big').textContent})()""")
        c.eq(r.replace('\xa0',' '), '€ 54,50', 'Lagerwert 5×8,5 + 250×0,048')

        # ---------- Intervall-Prognose ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});const v=await T.iv({carId:c.id,km:10000,months:null});
          await T.entry({carId:c.id,date:'2026-01-15',odo:100000,intervalIds:[v.id]});
          await T.entry({carId:c.id,date:'2026-07-15',odo:106000});
          const s=ivStatus(v);return{st:s.st,kmLeft:s.kmLeft,est:s.estDate,pct:Math.round(s.pct*100)}})()""")
        c.eq((r['st'], r['kmLeft'], r['pct']), ('ok', 4000, 60), 'Intervall 10.000 km: 6.000 gefahren')
        c.ok(r['est'] and r['est'].startswith('2026-1'), f'Prognose ≈ Okt./Nov. 2026 (ist {r["est"]})')

        # Intervall: letzter Eintrag ohne km, früherer mit km → km-Zählung bleibt
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});const v=await T.iv({carId:c.id,km:10000,months:12});
          await T.entry({carId:c.id,date:'2025-12-01',odo:100000,intervalIds:[v.id]});
          await T.entry({carId:c.id,date:'2026-06-01',odo:null,intervalIds:[v.id]});
          await T.entry({carId:c.id,date:'2026-09-01',odo:109000});
          const s=ivStatus(v);return{kmLeft:s.kmLeft,date:s.last.date}})()""")
        c.eq(r['date'], '2026-06-01', 'Intervall: letztes Datum')

        # Überfällig nach km, Datum noch nicht erreicht → „seit 46 km überfällig“ ohne verwirrendes „bis …“
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});const v=await T.iv({carId:c.id,km:15000,months:12});
          await T.entry({carId:c.id,date:addMonths(today(),-5),odo:181000,intervalIds:[v.id]});
          await T.entry({carId:c.id,date:today(),odo:196046});
          const s=ivStatus(v);return{st:s.st,text:s.text}})()""")
        c.eq(r['st'], 'over', 'km überschritten → überfällig')
        c.eq(r['text'].replace('\xa0', ' '), 'seit 46 km überfällig (fällig bei 196.000 km)', 'Text: seit wie vielen km überfällig + Fällig-km')
        # Überfällig nach Datum, km noch nicht erreicht → Tage statt „noch … km“
        await ev("T.reset()")
        r = await ev("""(async()=>{const c=await T.car({});const v=await T.iv({carId:c.id,km:15000,months:12});
          await T.entry({carId:c.id,date:addMonths(today(),-12).replace(/\\d\\d$/,'01'),odo:100000,intervalIds:[v.id]});
          await T.entry({carId:c.id,date:today(),odo:101000});
          const s=ivStatus(v);return{st:s.st,text:s.text,d:-s.daysLeft}})()""")
        c.ok(r['st'] == 'over' and r['text'].startswith('seit ') and f"({r['d']} Tag" in r['text'] and 'noch' not in r['text'], f"Datum überschritten: „seit … überfällig (n Tage)“ ({r['text']})")

        # ---------- Jahresrückblick: Teilelager-Einkäufe zählen zu den Ausgaben ----------
        await ev("T.reset()")
        r = await ev("""(async()=>{await put('inventory',{id:uid(),name:'Öl',qty:5,unit:'l',price:8,buys:[{id:uid(),date:'2026-03-01',qty:5,unit:'l',price:40}]});
          wrappedSheet('2026');const t=$('#sheet').textContent;closeSheet();return t})()""")
        c.ok('Teilelager' in r and '40,00' in r, 'Jahresrückblick zeigt Teilelager-Einkäufe')

        # ---------- leere DB: alle Seiten ohne Fehler ----------
        await ev("T.reset()")
        for h in ['#/home', '#/stats', '#/calendar', '#/tools', '#/inv', '#/shop', '#/more', '#/prices', '#/warranty', '#/archive']:
            await H.go(page, h)
        c.eq([e for e in page.errors], [], 'keine JS-Fehler')
        await b.close()
    return c.done()

if __name__ == '__main__':
    H.run(main)

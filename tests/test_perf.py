"""Tempo mit vielen Daten: 2 Autos, 1500 Einträge, 400 Tankungen, 120 Werkzeuge, 200 Lagerteile, 300 Fotos.

python3 tests/test_perf.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from playwright.async_api import async_playwright

GEN = r"""async()=>{
 // Testfoto ca. 1280×960 JPEG erzeugen (realistische Größe)
 const cv=document.createElement('canvas');cv.width=1280;cv.height=960;const g=cv.getContext('2d');
 for(let i=0;i<400;i++){g.fillStyle=`hsl(${i*37%360},50%,${30+i%40}%)`;g.fillRect(Math.random()*1280,Math.random()*960,120,90)}
 const jpg=cv.toDataURL('image/jpeg',.72);
 const cars=myCars();const ids=cars.map(c=>c.id);
 const ents=[],fuel=[],tools=[],inv=[],photos=[];
 for(let i=0;i<1500;i++){const d=new Date(2010,0,1+i*3);const ph=i%5===0?[{id:'ph'+i,tag:'Foto'}]:[];if(ph.length)photos.push({id:'ph'+i,data:jpg});
  ents.push({id:'e'+i,carId:ids[i%2],date:isoD(d),odo:100000+i*60,category:CATS[i%CATS.length],title:'Arbeit '+i,desc:'',diy:i%3>0,workshop:'',hours:1,labor:i%3?null:50,notes:'',
   parts:[{name:'Teil '+(i%40),maker:'Hersteller '+(i%9),partNo:'N'+i,qty:1,unit:'Stk',price:10+i%50,spec:'',shop:''}],photos:ph,intervalIds:[],toolIds:['t'+(i%120)]})}
 for(let i=0;i<400;i++){const d=new Date(2015,0,1+i*7);fuel.push({id:'f'+i,carId:ids[i%2],date:isoD(d),odo:150000+i*300,liters:40,price:60,ppl:1.5,type:'Diesel',station:'OMV',full:true,note:''})}
 for(let i=0;i<120;i++){tools.push({id:'t'+i,name:'Werkzeug '+i,category:TOOL_CATS[i%TOOL_CATS.length],price:50,rentPrice:10,extraUses:0,photoId:i<30?'tp'+i:null});if(i<30)photos.push({id:'tp'+i,data:jpg})}
 for(let i=0;i<200;i++)inv.push({id:'i'+i,name:'Lagerteil '+i,qty:3,unit:'Stk',price:5,fits:[]});
 const t=db.transaction(['entries','fuel','tools','inventory','photos'],'readwrite');
 for(const x of ents){t.objectStore('entries').put(x);S.entries.push(x)}for(const x of fuel){t.objectStore('fuel').put(x);S.fuel.push(x)}
 for(const x of tools){t.objectStore('tools').put(x);S.tools.push(x)}for(const x of inv){t.objectStore('inventory').put(x);S.inventory.push(x)}
 for(const x of photos)t.objectStore('photos').put(x);await txDone(t);return{photos:photos.length,mb:Math.round(photos.length*jpg.length/1048576)}}"""

TIME = """async(h)=>{const t0=performance.now();location.hash=h;await new Promise(r=>setTimeout(r,0));render();const t1=performance.now();
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return Math.round(t1-t0)}"""


async def main():
    c = H.Check('Tempo')
    base, srv = H.serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page = await H.open_app(b, base)
        info = await page.evaluate(GEN)
        print('Testdaten:', info)
        t0 = await page.evaluate("performance.now()")
        await page.reload(); await H.ready(page)
        cid = await page.evaluate("myCars()[0].id")
        res = {}
        for h in ['#/home', '#/cars', f'#/car/{cid}', f'#/car/{cid}/hist', f'#/car/{cid}/iv', f'#/car/{cid}/fuel', '#/ws', '#/tools', '#/inv', '#/stats', '#/calendar', '#/search', '#/more']:
            res[h] = await page.evaluate(TIME, h)
        await page.evaluate("A.homeTab({t:'log'})")
        res['Verlauf'] = await page.evaluate(TIME, '#/home')
        await page.evaluate("A.homeTab({t:'ov'})")
        res['Werkstatt alle aufgeklappt'] = await page.evaluate("""async()=>{location.hash='#/tools';await new Promise(r=>setTimeout(r,50));const t0=performance.now();A.toolGrpAll({o:'1'});return Math.round(performance.now()-t0)}""")
        res['Löschen mit Rückgängig'] = await page.evaluate("""async()=>{const t0=performance.now();await withUndo('entryDelete',()=>del('entries','e5'));return Math.round(performance.now()-t0)}""")
        res['Backup erstellen'] = await page.evaluate("""async()=>{const t0=performance.now();const j=await backupJSON();return Math.round(performance.now()-t0)+' ms, '+Math.round(j.length/1048576)+' MB'}""")
        mem = await page.evaluate("performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576)+' MB':'–'")
        for k, v in res.items():
            print(f'  {k:32s} {v} ms' if isinstance(v, int) else f'  {k:32s} {v}')
        print('  JS-Speicher', mem)
        for k, v in res.items():
            if isinstance(v, int):
                c.ok(v < 400, f'{k} unter 400 ms (ist {v} ms)')
        c.eq(page.errors, [], 'keine JS-Fehler')
        await b.close()
    return c.done()

if __name__ == '__main__':
    H.run(main)

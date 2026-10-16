import sys,asyncio,os,shutil;sys.path.insert(0,'/home/claude/automanager/tests')
import harness as H
from playwright.async_api import async_playwright
D='/tmp/claude-0/-home-claude/7c58c432-b40e-5693-b0a2-4a2d9dfee2ed/scratchpad/room/'
WS=open(D+'ws.js').read()
async def main():
    base,srv=H.serve()
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # Standbilder
        ctx,page=await H.open_app(b,base)
        await page.evaluate("(async()=>{const it=S.inventory.find(i=>i.minQty!=null);it.qty=0;await put('inventory',it);return 1})()")
        await page.evaluate(WS)
        for i,h in enumerate([11,18,22]):
            await H.go(page,'#/home');await H.go(page,'#/tools')
            await page.evaluate(f"WS.render($('#view'),{h})"); await page.wait_for_timeout(1500)
            await page.screenshot(path=D+f's{i}.png')
        print('stills',page.errors); await ctx.close()
        # Video
        vd=D+'vid'; shutil.rmtree(vd,ignore_errors=True)
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=1,has_touch=True,is_mobile=True,locale='de-AT',timezone_id='Europe/Vienna',service_workers='block',record_video_dir=vd,record_video_size={'width':390,'height':844})
        await ctx.add_init_script("try{localStorage.setItem('garage.installHide','1')}catch(e){}")
        page=await ctx.new_page(); page.errors=[]; page.on('pageerror',lambda e:page.errors.append(str(e)))
        await page.goto(base+'index.html#/home'); await H.ready(page)
        await page.evaluate("(async()=>{const it=S.inventory.find(i=>i.minQty!=null);it.qty=0;await put('inventory',it);return 1})()")
        await page.evaluate(WS); await H.go(page,'#/tools')
        await page.evaluate("WS.render($('#view'),11)"); await page.wait_for_timeout(1800)
        await page.evaluate("""new Promise(res=>{const t0=performance.now();(function f(){const t=(performance.now()-t0)/2600;WS.tilt(Math.sin(t*Math.PI*2),Math.sin(t*Math.PI*4)*.5);if(t<1)requestAnimationFrame(f);else{WS.tilt(0,0);res(1)}})()})""")
        await page.wait_for_timeout(500)
        await page.tap('#ws-tools .drawer1'); await page.wait_for_timeout(1500)
        await page.evaluate("scrollTo({top:300,behavior:'smooth'})"); await page.wait_for_timeout(900)
        await page.evaluate("scrollTo(0,0);history.replaceState(null,'','#/tools');WS.back($('#view'),11)"); await page.wait_for_timeout(1000)
        await page.tap('#ws-inv'); await page.wait_for_timeout(1600)
        await page.evaluate("WS.back($('#view'),11)"); await page.wait_for_timeout(900)
        await page.tap('#ws-shop'); await page.wait_for_timeout(1500)
        print('video',page.errors); await ctx.close(); await b.close()
        f=[x for x in os.listdir(vd) if x.endswith('.webm')][0]
        os.system(f"ffmpeg -loglevel error -y -i {vd}/{f} -vf 'crop=390:780:0:0,scale=390:-2' -c:v libx264 -pix_fmt yuv420p -movflags +faststart {D}werkstatt-raum.mp4")
asyncio.run(main())

#!/usr/bin/env python3
"""Holdout test runner. Run from the repo root:   python3 tests/run_tests.py
Needs: python3, `pip install playwright` + `playwright install chromium` (skip the install if Chromium is already there), node (for the syntax check).
Optional: `npm install` in tests/ puts three.js r128 locally so the game loads without internet.
It: 1) syntax-checks the game script  2) boots the game headless on the test map  3) checks movement, jumping,
rolling, every gun's aim (ADS + hip), weapon swaps, and that nothing threw an error. Screenshots go to tests/shots/.
Exit code 0 = all passed."""
import os,re,sys,json,time,math,threading,functools,subprocess,http.server
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));SHOTS=os.path.join(ROOT,'tests','shots');os.makedirs(SHOTS,exist_ok=True)
NM=os.path.join(ROOT,'tests','node_modules','three');PORT=int(os.environ.get('PORT','8765'))
FAILS=[];PASSES=[]
def ok(name,cond,info=''):
    (PASSES if cond else FAILS).append(name);print(('PASS ' if cond else 'FAIL ')+name+(('  '+str(info)) if info else ''),flush=True)

# ---------- 1. syntax ----------
src=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
js=max(re.findall(r'<script>(.*?)</script>',src,re.S),key=len)
tmp=os.path.join(ROOT,'tests','_game.js');open(tmp,'w',encoding='utf-8').write(js)
try:
    r=subprocess.run(['node','--check',tmp],capture_output=True,text=True);ok('syntax',r.returncode==0,r.stderr[:400])
except FileNotFoundError:print('SKIP syntax (node not installed)')
if FAILS:sys.exit(1)

# ---------- 2. build a test copy with hooks ----------
H=[("buildWeapon('club');setGameUI(false);applyTouchPref();loadSoldier();netInit();",
    "window.__E=c=>eval(c);window.__H={startGame,SOLD};buildWeapon('club');setGameUI(false);applyTouchPref();loadSoldier();netInit();"),
   ("let dt=Math.min(.05,(now-last)/1000);last=now;","let dt=window.__FIX?window.__FIX:Math.min(.05,(now-last)/1000);last=now;")]
qa=src
for a,b in H:
    if a not in qa:ok('test hooks still match the game code ('+a[:40]+'...)',False,'update tests/run_tests.py H list');sys.exit(1)
    qa=qa.replace(a,b)
open(os.path.join(ROOT,'qa.html'),'w',encoding='utf-8').write(qa)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT));threading.Thread(target=srv.serve_forever,daemon=True).start()

PAD="""(()=>{const mk=()=>({id:'Xbox Fake',index:0,connected:true,mapping:'standard',timestamp:0,axes:[0,0,0,0],buttons:Array.from({length:17},()=>({pressed:false,value:0,touched:false}))});
window.__pad=null;window.__padOn=()=>{window.__pad=mk()};const orig=navigator.getGamepads?navigator.getGamepads.bind(navigator):()=>[];
navigator.getGamepads=()=>window.__pad?[window.__pad]:orig();window.__btn=(i,v)=>{if(!window.__pad)return;window.__pad.buttons[i]={pressed:!!v,value:v?1:0,touched:!!v};window.__pad.timestamp++};
window.__ax=(i,v)=>{if(window.__pad){window.__pad.axes[i]=v;window.__pad.timestamp++}};try{localStorage.setItem('holdout-map','test')}catch(e){}})()"""

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    exe=os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') and os.path.isfile('/opt/pw-browsers/chromium') else None)
    b=pw.chromium.launch(executable_path=exe,args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':640,'height':400});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    if os.path.exists(NM):
        pg.route('**/three.min.js',lambda r:r.fulfill(path=NM+'/build/three.min.js'));pg.route('**/GLTFLoader.js',lambda r:r.fulfill(path=NM+'/examples/js/loaders/GLTFLoader.js'))
    pg.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(body=''))
    pg.add_init_script(PAD)
    pg.goto(f'http://127.0.0.1:{PORT}/qa.html')
    pg.wait_for_function('window.__H&&(__H.SOLD.ready||__H.SOLD.failed)',timeout=240000)
    x=lambda c:pg.evaluate('c=>__E(c)',c);e=pg.evaluate
    ok('character loaded',x('SOLD.ready'))
    e('__H.startGame(null)');pg.wait_for_function('document.getElementById("loading").hidden',timeout=240000);time.sleep(1.5)
    e("document.querySelectorAll('.ov').forEach(o=>{if(!o.hidden&&o.id!=='hud')o.hidden=true})")
    x("(SET.testRun=false,SET.testInf=false,0)")
    ok('Mixamo animations loaded',x("!!(MXL.data&&SOLD.BD&&SOLD.PS&&SOLD.RF&&SOLD.MXJ)"),x("JSON.stringify({BD:!!SOLD.BD,PS:!!SOLD.PS,RF:!!SOLD.RF,MXJ:!!SOLD.MXJ})"))
    def tp(px,pz,face):x(f"(P.x={px},P.z={pz},P.y=groundAt({px},{pz},5),P.vy=0,P.vx=P.vz=0,P.speed=0,P.yaw={face}+Math.PI,P.face={face},P.act=null,P.roll=null,P.onGround=true,S.crouch=false,0)")
    e("window.__padOn()");time.sleep(.5)
    # movement
    tp(-24,26.8,math.pi/2);e("window.__ax(1,-1)");time.sleep(2.5);sp=x("P.speed");e("window.__ax(1,0)");time.sleep(1)
    ok('sprint speed in range (5.5-8.5 m/s)',5.5<sp<8.5,round(sp,2))
    pg.screenshot(path=SHOTS+'/move.png')
    # jump + roll
    tp(-24,26.8,math.pi/2);e("window.__btn(0,1)");time.sleep(.12);e("window.__btn(0,0)");time.sleep(.25);air=not x("P.onGround");time.sleep(1.5)
    ok('jump leaves the ground',air)
    e("window.__btn(1,1)");time.sleep(.08);e("window.__btn(1,0)");time.sleep(.1);e("window.__btn(1,1)");time.sleep(.08);e("window.__btn(1,0)");time.sleep(.2);rolled=x("!!P.roll");time.sleep(1.5)
    ok('double-tap B rolls',rolled)
    # guns: ADS and hip aim must point at the crosshair
    M="""(()=>{const q=weaponMesh.getWorldQuaternion(new THREE.Quaternion()),v=new THREE.Vector3(0,-1,0).applyQuaternion(q),c=AIMCAM.d;return JSON.stringify([Math.asin(v.y)*57.3,Math.asin(c.y)*57.3,Math.atan2(v.x,v.z)*57.3,Math.atan2(c.x,c.z)*57.3])})()"""
    def diff(m):
        p,cp,y,cy=json.loads(m);dy=abs(((y-cy+180)%360)-180);return abs(p-cp),dy
    tp(-24,26.8,math.pi/2)
    for g in ['pistol','revolver','shotgun','smg','ar','sniper']:
        x(f"(equip('{g}'),0)");time.sleep(1.4)
        e("window.__btn(7,1)");time.sleep(.1);e("window.__btn(7,0)");time.sleep(.12)   # hip fire one shot, then take the best of a few samples (recoil kick settles, gun lowers ~0.8 s later)
        best=None
        for _ in range(6):
            d=diff(x(M));best=d if best is None or d[0]+d[1]<best[0]+best[1] else best;time.sleep(.05)
        dp,dy=best;ok(f'{g} hip-fire aim on crosshair (<5 deg)',dp<5 and dy<5,f'pitch off {dp:.1f}, yaw off {dy:.1f}')
        e("window.__btn(6,1)");time.sleep(1.3);dp,dy=diff(x(M));ok(f'{g} ADS aim on crosshair (<3 deg)',dp<3 and dy<3,f'pitch off {dp:.1f}, yaw off {dy:.1f}')
        pg.screenshot(path=SHOTS+f'/ads_{g}.png');e("window.__btn(6,0)");time.sleep(.4)
    x("(equip('axe'),0)");time.sleep(1)
    ok('no JavaScript errors',len(errs)==0,errs[:5])
    b.close()
srv.shutdown()
try:os.remove(os.path.join(ROOT,'qa.html'));os.remove(tmp)
except Exception:pass
print(f'\n{len(PASSES)} passed, {len(FAILS)} failed');sys.exit(1 if FAILS else 0)

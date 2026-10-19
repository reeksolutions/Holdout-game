import sys,json,threading,http.server,functools,socketserver
from playwright.sync_api import sync_playwright
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory='/root/work')
class Q(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
socketserver.TCPServer.allow_reuse_address=True
srv=socketserver.ThreadingTCPServer(('127.0.0.1',8890),functools.partial(Q,directory='/root/work'));threading.Thread(target=srv.serve_forever,daemon=True).start()
jobs=[a.split('=') for a in sys.argv[1:]]   # name=file.fbx
out={}
try:out=json.load(open('/root/work/srv/mx_anims.json'))
except Exception:pass
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader']);p=b.new_page();p.on('console',lambda m:print('C:',m.text))
  p.goto('http://127.0.0.1:8890/mx/rt.html');p.wait_for_function('typeof window.run==="function"')
  print('UAL',p.evaluate("ual(['Idle_Loop','Walk_Loop','Jog_Fwd_Loop','Sprint_Loop','Crouch_Fwd_Loop','Crouch_Idle_Loop'],30)"))
  for n,f in jobs:
    r=p.evaluate(f"run('/mx/{f}','{n}',30)");print(n,round(r['dur'],2),'spd',r['spd'],r['bones']);out[n]=r
json.dump(out,open('/root/work/srv/mx_anims.json','w'),separators=(',',':'))
import os;print(os.path.getsize('/root/work/srv/mx_anims.json'))

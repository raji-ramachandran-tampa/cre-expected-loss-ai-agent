"""Loopback-only local review interface; no secrets sent to the browser."""
import json
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from workbench import Workbench, ROOT, DEFAULT_TASK, encode
from demonstrations import demonstrate
from governance import policy, tool_decision
from lgd_comparison import compare_existing_lgd

lock = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(60)

    def log_message(self, *args):
        pass

    def send(self, value, status=200, content_type='application/json'):
        body = value.encode() if isinstance(value,str) else encode(value).encode()
        self.send_response(status)
        self.send_header('Content-Type',content_type+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def dispatch(self, method):
        # Reject cross-origin writes and DNS-rebinding requests.
        if self.headers.get('Host') != '127.0.0.1:8765':
            self.send({'error':'Invalid host'},403)
            return
        if method=='POST' and self.headers.get('Origin') not in (None,'http://127.0.0.1:8765'):
            self.send({'error':'Invalid origin'},403)
            return
        if method=='GET' and self.path=='/':
            self.send((ROOT/'index.html').read_text(encoding='utf-8'),content_type='text/html')
            return
        with lock:
            app=Workbench()
            try:
                if method=='GET':
                    if self.path=='/api/runs':
                        value=app.listing()
                    elif self.path=='/api/governance':
                        value=policy()
                    elif self.path=='/api/reference':
                        value=app.references()
                    elif self.path.startswith('/api/run/'):
                        value=app.inspect(self.path.split('/')[-1])
                    else:
                        self.send({'error':'Not found'},404)
                        return
                else:
                    length=int(self.headers.get('Content-Length','0'))
                    if length>12000:
                        raise ValueError('Request too large')
                    data=json.loads(self.rfile.read(length))
                    if self.path=='/api/create':
                        key=app.create(task=data.get('task') or DEFAULT_TASK,scope=data.get('scope','demo'),provider=data.get('provider','offline'),budget=data.get('budget',0.05),inject=data.get('inject',False))
                        value=app.inspect(key)
                    elif self.path=='/api/step':
                        value=app.step(data['id'])
                    elif self.path=='/api/finish':
                        value=app.finish(data['id'])
                    elif self.path=='/api/memory':
                        value={'id':app.remember(data['scope'],data['text'],'user-entered local preference',float(data.get('ttl',86400)))}
                    elif self.path=='/api/demonstrate':
                        value=demonstrate(data['name'])
                    elif self.path=='/api/governance/check':
                        choices={'allowed':('ead',{'case_id':'amortization'}),'private_data':('ead',{'current_balance':100,'borrower':'example'}),'unapproved_tool':('shell',{}),'agent_approval':('approve_model',{})}
                        name,args=choices[data['example']]
                        value=tool_decision(name,args)
                        app.event('governance-demonstration','governance_decision',{'example':data['example'],**value})
                    elif self.path=='/api/lgd/comparison':
                        decision=tool_decision('lgd_compare',{'comparison_id':'signed_lgd_research_2026Q1'})
                        app.event('lgd-comparison','governance_decision',decision)
                        if not decision['allowed']:
                            raise ValueError(decision['reason'])
                        value=compare_existing_lgd()
                        app.event('lgd-comparison','tool_result',value)
                    else:
                        self.send({'error':'Not found'},404)
                        return
                self.send(value)
            except Exception as exc:
                self.send({'error':type(exc).__name__+': '+str(exc)},400)
            finally:
                app.close()

    def do_GET(self):
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

if __name__=='__main__':
    print('CRE Expected Loss AI Agent: http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()

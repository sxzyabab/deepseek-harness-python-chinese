import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlparse
from hmac import compare_digest
from .输入 import 语音输入错误

__all__=['启动识别服务器']

def 启动识别服务器(令牌,最大音频字节,转写):
    """绑定临时环回监听；模型加载完成后再公布就绪。"""
    期望=('Bearer '+令牌).encode('utf-8')
    class 处理(BaseHTTPRequestHandler):
        """私有认证转写入口。"""
        def log_message(自身,*位置参数):
            """不向 stderr 打访问日志。"""
            return
        def 回复(自身,状态,值):
            """JSON 应答。"""
            体=json.dumps(值).encode('utf-8')
            自身.send_response(状态)
            自身.send_header('content-type','application/json')
            自身.send_header('content-length',str(len(体)))
            自身.end_headers()
            自身.wfile.write(体)
        def do_POST(自身):
            """只接受 /transcribe。"""
            授权=(自身.headers.get('authorization') or '').encode('utf-8')
            if len(授权)!=len(期望) or not compare_digest(授权,期望):
                自身.回复(401,{'error':'Unauthorized'})
                return
            解析=urlparse(自身.path)
            if 解析.path!='/transcribe':
                自身.回复(404,{'error':'Unknown endpoint'})
                return
            长度文本=自身.headers.get('content-length')
            try:
                长度=int(长度文本)
            except (TypeError,ValueError):
                自身.回复(413,{'error':'Invalid speech audio size','code':'invalid-input'})
                return
            if 长度<46 or 长度>最大音频字节:
                自身.回复(413,{'error':'Invalid speech audio size','code':'invalid-input'})
                return
            音频=自身.rfile.read(长度)
            语言=(parse_qs(解析.query).get('language') or ['auto'])[0]
            try:
                自身.回复(200,转写(音频,语言))
            except 语音输入错误 as 错误:
                自身.回复(400,{'error':str(错误),'code':'invalid-input'})
            except Exception as 错误:
                自身.回复(500,{'error':str(错误)})
        def do_GET(自身):
            """未知。"""
            自身.回复(404,{'error':'Unknown endpoint'})
    服务器=ThreadingHTTPServer(('127.0.0.1',0),处理)
    return {'server':服务器,'port':服务器.server_address[1]}

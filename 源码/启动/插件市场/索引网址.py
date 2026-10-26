'索引源网址的校验；设置索引与每次读取共用'
import re#主机与片段
from urllib.parse import urlparse#拆网址
from ...类型化远程调用.协议 import 远程错误#远程拒绝

__all__=['规范化索引网址']#仅中文公开名

def 拒绝(文本,理由,说明):
    'plugin-market/invalid-index-url；说明原样上报'
    raise 远程错误('plugin-market/invalid-index-url',说明,{'url':文本,'reason':理由})#拒绝

def 序列化网址(解析):
    '对齐 URL.href：小写主机、空路径补斜杠、默认端口省略'
    主机=解析.hostname.lower() if isinstance(解析.hostname,str) else ''#主机
    if ':' in 主机:#IPv6
        主机='['+主机+']'#括号
    端口=解析.port#端口
    if 端口 is not None and not ((解析.scheme=='https' and 端口==443) or (解析.scheme=='http' and 端口==80)):#非默认
        主机=主机+':'+str(端口)#带端口
    路径=解析.path if 解析.path else '/'#空路径
    查询='' if 解析.query=='' else '?'+解析.query#查询
    return 解析.scheme+'://'+主机+路径+查询#序列化

def 规范化索引网址(文本):
    '校验并收成规范形式。只接受不带凭据、不带片段的 http(s)'
    修剪=文本.strip()#去掉两端空白
    解析=urlparse(修剪)#拆开
    if 解析.scheme=='' or 解析.netloc=='':#不是绝对网址
        拒绝(文本,'not-absolute','Not an absolute URL: '+文本)#上报原文
    if 解析.scheme!='https' and 解析.scheme!='http':#方案
        拒绝(文本,'scheme','Index URLs use http or https: '+文本)#方案
    if (解析.username not in (None,'') or 解析.password not in (None,'') or 解析.fragment!=''
            or '#' in 修剪):#凭据或片段
        拒绝(文本,'credentials-or-fragment','Index URLs carry no credentials or fragment: '+文本)#拒绝
    if re.search(r'\s',修剪) is not None:#空白
        拒绝(文本,'not-absolute','Not an absolute URL: '+文本)#与模式一致
    return 序列化网址(解析)#规范形式

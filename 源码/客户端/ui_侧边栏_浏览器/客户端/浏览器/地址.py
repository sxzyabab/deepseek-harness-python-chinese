import re#地址方案探测
from urllib.parse import urlparse as 解析URL,urlunparse as 组合URL#标准库 URL

__all__=['最大地址字节','解析浏览器地址']#仅中文公开名

最大地址字节=16*1024#地址上限，约束持久化导航状态

_显式方案=re.compile(r'^[A-Za-z][A-Za-z\d+.-]*:(?!\d+(?:[/?#]|$))',re.ASCII)#显式 scheme

def 解析浏览器地址(输入,应用源=None):
    """把地址栏值解析进固定协议白名单。返回目标 dict 或拒因。"""
    修剪=输入.strip()#去空白
    if 修剪=='':#空
        return {'ok':False,'reason':'empty'}#空地址
    if len(修剪.encode('utf-8'))>最大地址字节:#超长按 UTF-8 字节
        return {'ok':False,'reason':'invalid'}#无效
    显式=_显式方案.search(修剪) is not None#是否带方案
    候选=修剪 if 显式 else f'https://{修剪}'#缺省补 https
    try:#解析 URL
        址=解析URL(候选)#解析
    except ValueError:#畸形
        return {'ok':False,'reason':'invalid'}#无效
    if 址.scheme=='' or 址.netloc=='':#畸形
        return {'ok':False,'reason':'invalid'}#无效
    用户名=址.username if 址.username is not None else ''#用户
    密码=址.password if 址.password is not None else ''#密码
    if 用户名!='' or 密码!='':#含凭据
        return {'ok':False,'reason':'credentials'}#拒绝凭据
    协议=址.scheme.lower()+':'#带冒号协议
    if 协议!='https:' and 协议!='http:':#协议拒绝
        return {'ok':False,'reason':'protocol'}#拒
    if 应用源 is not None and 应用源!='null':#有应用源
        try:#比较源
            应用=解析URL(应用源)#应用 URL
            应用源串=f'{应用.scheme}://{应用.netloc}'#应用 origin
            目标源=f'{址.scheme}://{址.netloc}'#目标 origin
            if 目标源==应用源串:#同源
                return {'ok':False,'reason':'application-origin'}#拒应用自身
        except ValueError:#应用源不可用
            pass#不能因此放行
    完整=组合URL(址)#规范化 href
    标题=址.hostname if 址.hostname is not None else ''#主机名
    return {'ok':True,'target':{#接受
        'kind':'https' if 协议=='https:' else 'http',#种类
        'url':完整,#规范址
        'title':标题,#标题
    }}#目标结束

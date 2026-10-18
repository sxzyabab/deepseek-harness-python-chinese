'页面上的已安装应用、上次选择，以及打开工作区目录的请求。'
from ...模块.客户端.通告 import 取握手窗口
import json
import threading
from ...存储 import 创建快照存储
from ....宿主.在应用中打开.共享 import 应用列表路由,打开路由
from .应用列表 import 应用标签键

__all__=['等到','读取','在应用中打开控制器']

线程事件=threading.Event


def 等到(产出):
    '浏览器期约阻塞到结算。已经是值就直接返回'
    然后=getattr(产出,'then',None)
    if not callable(然后):
        return 产出
    完成=线程事件()
    盒子={}

    def 成功(结果=None):
        '期约兑现'
        盒子['值']=结果
        完成.set()

    def 失败(错误=None):
        '期约拒绝'
        if isinstance(错误,BaseException):
            盒子['错误']=错误
        elif 错误 is None:
            盒子['错误']=Exception('rejected')
        else:
            盒子['错误']=Exception(str(错误))
        完成.set()

    然后(成功,失败)
    完成.wait()
    if '错误' in 盒子:
        raise 盒子['错误']
    return 盒子.get('值')


def 读取(对象,键):
    '字典用键，浏览器对象用同名属性'
    if isinstance(对象,dict):
        return 对象.get(键)
    return getattr(对象,键)


class 在应用中打开控制器:
    '每页读一次已安装应用，记住选择，并把打开请求交给主机'
    def __init__(自身,取数=None):
        '缺省用浏览器 fetch'
        if 取数 is None:
            def 浏览器取数(输入,初始化=None):
                '这个网页引擎不再通过浏览器请求宿主'
                raise RuntimeError('这个网页引擎不再通过浏览器请求宿主 '+str(输入))
            自身.取数=浏览器取数
        else:
            自身.取数=取数
        自身.应用表=创建快照存储(None)
        自身.选择=创建快照存储('',{'persist':{'name':'dsh.open-in-app.choice'}})
        自身.操作=创建快照存储({'phase':'idle','path':None})
        自身.加载中=None

    def 当前应用(自身):
        '记住的、并且还能命名的应用。没有就用列表第一项'
        表=自身.应用表.getSnapshot()
        if 表 is None:
            表=[]
        可用=[]
        for 标识 in 表:
            if 标识 in 应用标签键:
                可用.append(标识)
        选择=自身.选择.getSnapshot()
        if 选择 in 可用:
            return 选择
        if len(可用)==0:
            return None
        return 可用[0]

    def 加载(自身):
        '每个控制器只读一次。失败发布空列表，按钮不出现'
        if 自身.加载中 is not None:
            return
        自身.加载中=True
        自身.跑()

    def 选定(自身,应用标识):
        '记住这次选的应用。正在打开时不改'
        if 自身.操作.getSnapshot()['phase']!='busy':
            自身.选择.set(应用标识)

    def 启动(自身,应用标识,路径):
        '用这个应用打开工作区目录。进行中的请求忽略。失败时阶段写成 error 再抛出'
        if 自身.操作.getSnapshot()['phase']=='busy':
            return
        自身.操作.set({'phase':'busy','path':路径})
        正文={'app':应用标识,'path':路径}
        try:
            响应=等到(自身.取数(打开路由,{
                'method':'POST',
                'headers':{'content-type':'application/json'},
                'body':json.dumps(正文,ensure_ascii=False,separators=(',',':')),
            }))
            if not 读取(响应,'ok'):
                raise Exception('open failed: HTTP '+str(读取(响应,'status')))
            自身.操作.set({'phase':'idle','path':路径})
        except Exception:
            自身.操作.set({'phase':'error','path':路径})
            raise

    def 跑(自身):
        '读已安装应用。到不了主机就当成没有应用'
        应用=[]
        try:
            响应=等到(自身.取数(应用列表路由,{
                'headers':{'accept':'application/json'},
            }))
            if 读取(响应,'ok'):
                载荷=等到(响应.json())
                表=读取(载荷,'apps')
                if isinstance(表,list):
                    留下=[]
                    for 标识 in 表:
                        if isinstance(标识,str):
                            留下.append(标识)
                    应用=留下
        except Exception:
            应用=[]
        自身.应用表.set(应用)

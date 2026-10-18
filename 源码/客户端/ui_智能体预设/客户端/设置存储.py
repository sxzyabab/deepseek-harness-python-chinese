from ...存储 import 创建快照存储#快照仓
from ..异常 import 远程消息#失败句
from .文案 import 是否内置预设#出厂预设

__all__=['设置命名空间','写默认预设','需要编码工具','读名册','预设选项','等返回','预设设置控制器']

设置命名空间='agent-preset-registry'#宿主设置命名空间
空名册={'presets':[]}#没有这份服务时的空名册
初始={'status':'idle','error':None,'options':[]}#显示面初始快照

def 等返回(值):
    '上游 await 的同步等待。对象带等待方法就等它交回结果'
    等待=getattr(值,'等待',None)#等待方法
    if callable(等待):#有
        return 等待()#交回结果
    return 值#已经是结果

def 写默认预设(上下文,标识,期望修订=None):
    '把一份预设写成此后新建会话的默认。失败返回文案，成功返回 None'
    补丁={'selectedDefault':标识}#字段
    if 期望修订 is None:#不设篱笆
        应答=等返回(上下文.remote.settings.update(设置命名空间,补丁))#写入
    else:#自动纠正带上上次读到的修订
        应答=等返回(上下文.remote.settings.update(设置命名空间,补丁,期望修订))#写入
    if 应答.get('ok'):#成功
        return None#没有失败句
    return 远程消息(应答.get('error'))#失败句

def 需要编码工具(预设):
    '只有内置 PTC 和极简依赖编码工具偏好'
    if 预设 is None:#没有
        return False#不需要
    if 是否内置预设(预设) is not True:#自写预设自管
        return False#不需要
    return 预设['id']=='ptc' or 预设['id']=='minimal'#这两份

def 读名册(上下文):
    '读名册。没有这份服务时当作空名册，其它拒绝带回失败句'
    结果=等返回(上下文.remote.agentPresets.list())#名单
    if 结果.get('ok'):#成功
        return {'ok':True,'value':结果['value']}#名册
    错误=结果.get('error')#拒绝
    码=错误.get('code') if isinstance(错误,dict) else getattr(错误,'code',None)#码
    if 码=='gateway/invocation-unavailable':#部署没挂这份服务
        return {'ok':True,'value':空名册}#空名册
    return {'ok':False,'error':远程消息(错误)}#失败句

def 预设选项(预设列):
    '只留下能选的健康预设。坏掉的不进芯片和页眉'
    结果=[]#选项
    for 预设 in 预设列:#逐条
        if 预设.get('broken') is not None:#加载失败
            continue#跳过
        项={'id':预设['id']}#标识
        if 预设.get('name') is not None:#有自写名
            项['name']=预设['name']#带上
        if 预设.get('description') is not None:#有自写说明
            项['description']=预设['description']#带上
        结果.append(项)#一条
    return 结果#顺序与名册相同

class 预设设置控制器:
    '给页眉标签和创建插件菜单读名册'
    def __init__(自身,上下文):
        '记下上下文和空快照'
        自身.上下文=上下文#远程
        自身.存储=创建快照存储(dict(初始))#快照

    def _合并(自身,补丁):
        '浅合并后整份换上'
        下一=dict(自身.存储.getSnapshot())#拷贝
        下一.update(补丁)#补丁
        自身.存储.set(下一)#换上

    def 加载(自身):
        '读名册。空名册是没有预设的部署，页面不画。已经在读就返回'
        之前=自身.存储.getSnapshot()#当前
        if 之前['status']=='loading':#已经在读
            return#别人拥有这次
        自身._合并({'status':'loading','error':None})#开始
        名册=读名册(自身.上下文)#名册
        if 名册['ok'] is not True:#失败已是句子
            自身._合并({'status':'error','error':名册['error']})#写上
            return#停
        预设列=名册['value']['presets']#行
        if len(预设列)==0:#部署没有预设
            自身._合并({'status':'unavailable','options':[]})#不画
            return#停
        自身._合并({'status':'ready','error':None,'options':预设选项(预设列)})#可显示

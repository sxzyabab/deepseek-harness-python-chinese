from ...存储 import 创建快照存储#快照仓
from ..异常 import 远程消息#失败句
from .文案 import 中文#标准模式不可用
from .设置存储 import 写默认预设,需要编码工具,等返回,设置命名空间#默认预设

__all__=['分区控制器']

初始={'status':'idle','error':None,'saving':False,'rows':[],'view':None}#设置页初始快照

class 分区控制器:
    '设置页的名册、新任务默认，以及一次只看一份组装'
    def __init__(自身,上下文):
        '记下上下文和空快照'
        自身.上下文=上下文#远程与设置
        自身.存储=创建快照存储(dict(初始))#快照
        自身.在读=False#名册读取进行中
        自身.待保存=None#保存进行中
        自身.查看请求=0#查看世代

    def _合并(自身,补丁):
        '浅合并后整份换上'
        下一=dict(自身.存储.getSnapshot())#拷贝
        下一.update(补丁)#补丁
        自身.存储.set(下一)#换上

    def 加载(自身):
        '刷新名册。已经在读的调用不再另开一次'
        if 自身.在读:#已经在读
            return#共享这一次
        自身.在读=True#占住
        try:#读完才放开
            自身._读名册()#读
        finally:#无论成败
            自身.在读=False#放开

    def _读名册(自身):
        'list 失败写到页面上。这里不把未挂载服务当成空名册'
        try:#远程
            结果=等返回(自身.上下文.remote.agentPresets.list())#名单
            if 结果.get('ok') is not True:#拒绝
                raise Exception(远程消息(结果.get('error')))#交给下面
            自身._合并({'status':'ready','error':None,'rows':结果['value']['presets']})#行
        except Exception as 错误:#失败句
            自身._合并({'status':'error','error':远程消息(错误)})#写上

    def 查看(自身,标识):
        '打开一份预设的组装。被关掉或被下一次查看盖掉的结果丢掉'
        自身.查看请求=自身.查看请求+1#新世代
        请求=自身.查看请求#钉住
        自身._合并({'error':None,'view':None})#先清
        try:#远程
            结果=等返回(自身.上下文.remote.agentPresets.read(标识))#组装
            if 请求!=自身.查看请求:#已过期
                return#丢掉
            if 结果.get('ok') is not True:#拒绝
                raise Exception(远程消息(结果.get('error')))#交给下面
            值=结果['value']#正文
            名=标识 if 值.get('name') is None else 值['name']#标题
            自身._合并({'view':{'id':标识,'title':名,'content':值['content']}})#打开
        except Exception as 错误:#仍是这一次才写
            if 请求==自身.查看请求:#未过期
                自身._合并({'error':远程消息(错误)})#写上

    def 关闭查看(自身):
        '关掉查看器，并作废还没回来的读取'
        自身.查看请求=自身.查看请求+1#作废
        自身._合并({'view':None})#清

    def 设为默认(自身,标识,同步=None):
        '写成默认。同步回调只在空白会话仍在时套用'
        def 写入():
            '不带修订篱笆'
            return 写默认预设(自身.上下文,标识)#写入
        自身._保存(写入,同步)#保存

    def 对齐编码工具(自身,应重置):
        '编码工具关掉后，藏起来的内置默认改回标准。错误留在这一页'
        if 自身.待保存 is not None:#保存还没完
            等返回(自身.待保存)#等它
        if 应重置() is not True:#工具开着或本页已拆
            return#不动
        设置=自身.上下文.configForms.get(设置命名空间).getSnapshot()#预设设置
        if 设置.get('status')!='ready' or 设置.get('writable') is not True or 设置.get('revision') is None:#不能写
            return#停
        自身.加载()#最新名册
        if 应重置() is not True or 自身.存储.getSnapshot()['status']!='ready':#期间变了
            return#停
        行列=自身.存储.getSnapshot()['rows']#行
        默认行=None#当前默认
        for 行 in 行列:#找
            if 行.get('isDefault'):#默认
                默认行=行#记下
                break#停
        if 需要编码工具(默认行) is not True:#不用改
            return#停
        有标准=False#标准是否健康
        for 行 in 行列:#找标准
            if 行.get('id')=='standard' and 行.get('broken') is None:#能用
                有标准=True#有
                break#停
        if 有标准 is not True:#恢复不了
            自身._合并({'error':中文['standardUnavailable']})#页面上的句子
            return#停
        def 写入标准():
            '用关掉工具前读到的修订当篱笆'
            return 写默认预设(自身.上下文,'standard',设置['revision'])#写回标准
        自身._保存(写入标准)#保存

    def _保存(自身,写入,同步=None):
        '先写设置，再重读名册，然后按需同步空白会话'
        if 自身.存储.getSnapshot()['saving']:#已经在写
            return#忽略
        自身.待保存=True#占住
        自身._合并({'saving':True,'error':None})#写中
        try:#写和同步
            错误=写入()#设置
            自身.加载()#重读
            if 错误 is not None:#设置没接受
                raise Exception(错误)#交给下面
            选中=None#新的默认
            for 行 in 自身.存储.getSnapshot()['rows']:#找
                if 行.get('isDefault'):#默认
                    选中=行#记下
                    break#停
            if 选中 is not None and 同步 is not None:#还要套到空白会话
                同步错误=同步(选中['id'])#套用
                if 同步错误 is not None:#宿主拒绝
                    raise Exception(同步错误)#交给下面
        except Exception as 错误:#失败句留在页面上
            自身._合并({'error':远程消息(错误)})#写上
        finally:#结束这次保存
            自身.待保存=None#放开
            自身._合并({'saving':False})#不再写

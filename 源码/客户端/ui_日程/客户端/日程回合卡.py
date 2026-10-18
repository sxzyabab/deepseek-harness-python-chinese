'回合尾列出这一回合创建的任务，并用目录判断是不是还在'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .日程创建卡 import 日程创建卡
from .日程创建模型 import 日程创建卡模型
from .日程回合 import 创建工具

__all__=['日程回合卡']

样式模块='schedule-turn-card'

def 确保样式(文档):
    '回合卡列表样式只插一次'
    注入模块样式文件(文档,'日程回合卡样式',os.path.join(os.path.dirname(__file__),'日程回合卡.module.css'),样式模块)

def 选出任务(属性):
    '用回合结束序号截断。没有结束序号就用业主自己的序号'
    回合=属性['turn']
    数据=回合['data'].get('schedule-created') if hasattr(回合.get('data'),'get') else None
    序号=属性['seq']
    结束=回合.get('end')
    if isinstance(结束,dict) and 'seq' in 结束:
        序号=结束['seq']
    if 数据 is None:
        return None
    留下=[项 for 项 in 数据.get('created',[]) if 项.get('seq',0)<=序号]
    if len(留下)==0:
        return None
    return 留下

class 日程回合卡:
    '这一回合没创建任务就什么都不画'
    按回合={}

    def __new__(类,属性=None):
        '同一回合复用列表，挂上后请求一次更新的目录读取'
        回合=属性.get('turn') if isinstance(属性,dict) else None
        键=None if not isinstance(回合,dict) else 回合.get('id',回合.get('turn'))
        已有=类.按回合.get(键)
        if 已有 is not None and 已有.根 is not None and getattr(已有.根,'isConnected',False):
            已有.属性=属性
            return 已有.渲染()
        自身=object.__new__(类)
        自身.属性=属性
        自身.根=None
        自身.已请求=False
        自身.挂上请求=None
        自身.已订=False
        if 键 is not None:
            类.按回合[键]=自身
        return 自身.渲染()

    def 渲染(自身):
        '目录在挂上之后成功读过，缺记录才算已删除'
        属性=自身.属性
        创建=选出任务(属性)
        if 创建 is None:
            return None
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if not 自身.已订 and callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
            def 变更():
                '目录变了就重画'
                自身.渲染()
            属性['useCatalog']._subscribe(变更)
            自身.已订=True
        def 全取(快照):
            '整份目录快照'
            return 快照
        目录=属性['useCatalog'](全取)
        if not 自身.已请求:
            自身.挂上请求=目录.get('readRequest',0)
            自身.已请求=True
            属性['onRetry'](自身.挂上请求)
        记录=None
        if 目录.get('settled') and 目录.get('readSettled',0)>自身.挂上请求:
            记录=目录.get('records',[])
        if 自身.根 is None:
            根=文档.createElement('div')
            根.className='list'
            标样式模块(根,样式模块)
            自身.根=根
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        for 块 in 创建:
            任务=日程创建卡模型(块,创建工具)['task']
            当前=None
            传入={}
            if 任务 is None or 记录 is None:
                当前缺席=True
            else:
                当前缺席=False
                找到=None
                for 项 in 记录:
                    if 项.get('id')==任务['id']:
                        找到=项
                        break
                当前=找到
            卡片属性={
                'window':窗口,
                'callId':块.get('callId'),
                'toolName':创建工具,
                'block':块,
                'openTaskDetail':属性.get('openTaskDetail'),
            }
            if not 当前缺席:
                卡片属性['currentTask']=当前
            节点=日程创建卡(卡片属性)
            if 节点 is not None:
                自身.根.appendChild(节点)
        return 自身.根

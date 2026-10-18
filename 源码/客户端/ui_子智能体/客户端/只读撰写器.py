import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,模块节点

__all__=['只读撰写器']

样式模块='subagent-readonly-composer'

class 只读撰写器:
    '说明为何普通撰写器不可用'
    def __init__(自身,属性):
        '记下认领原因。有 window 就画出只读条'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '一次性、未知模式、父会话离线各一句中文'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        if 'window' not in 属性 or 'matched' not in 属性:
            return None
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '只读撰写器样式',
            os.path.join(os.path.dirname(__file__),'只读撰写器.module.css'),
            样式模块,
        )
        原因=属性['matched']['reason']
        一次性=原因=='one-shot'
        if 一次性:
            标题='一次性子智能体记录'
        else:
            标题='此子智能体暂时只读'
        if 原因=='unknown':
            正文='读取子会话后才能确定是否可继续。'
        elif 一次性:
            正文='一次性任务不支持后续消息，可在这里查看完整执行记录。'
        else:
            正文='父会话当前不在线，重新打开父会话后即可继续发送消息。'
        根=模块节点(文档,'div',样式模块,'frame')
        根.setAttribute('role','status')
        题=文档.createElement('strong')
        题.textContent=标题
        文=文档.createElement('span')
        文.textContent=正文
        根.appendChild(题)
        根.appendChild(文)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根

    def __call__(自身,属性=None):
        '槽位再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

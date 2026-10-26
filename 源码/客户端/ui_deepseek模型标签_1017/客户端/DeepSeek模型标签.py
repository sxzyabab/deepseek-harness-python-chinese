'两个官方 DeepSeek 通道上的临时 1017 角标。目录名和请求标识不变'
import os
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.标签 import 标签
from .文案 import 中文句

__all__=['DeepSeek模型标签']

样式模块='deepseek-model-label'
模型名='DeepSeek-V4.1-Flash'

class DeepSeek模型标签:
    '只给认得出的官方 Flash 条目加上 1017。其余目录名原样'
    def __init__(自身,属性):
        '记下提供方和模型，并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '官方账号或官方密钥，且模型标识与目录名都对上，才加角标'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            'DeepSeek模型标签样式',
            os.path.join(os.path.dirname(__file__),'DeepSeek模型标签.module.css'),
            样式模块,
        )
        提供方=属性.get('provider') or {}
        模型=属性.get('model') or {}
        目录名='' if 模型.get('name') is None else str(模型['name'])
        官方=提供方.get('id') in ('deepseek-account','deepseek-official')
        命中=官方 and 模型.get('id')=='deepseek-flash' and 目录名==模型名
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        if 命中 is not True:
            根=文档.createTextNode(目录名)
        else:
            根=文档.createElement('span')
            根.className='label'
            标样式模块(根,样式模块)
            名=文档.createElement('span')
            名.textContent=目录名
            根.appendChild(名)
            根.appendChild(文档.createTextNode(' '))
            角标=标签({
                'window':窗口,
                'tone':'info',
                'children':中文句('badge.label'),
            }).渲染()
            if 角标 is not None:
                根.appendChild(角标)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and hasattr(根,'parentNode') and 根.parentNode is not 父:
            父.appendChild(根)
        return 根

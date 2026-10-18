'present 调用的状态行，以及可展开的结果文本'
import json
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 描边图标
from ...ui_基础界面组件.披露行 import 披露行
from ....基础设施.通用工具 import 紧凑json编码
from .文案 import 中文

__all__=['呈现行']

样式模块='PresentRow'
样式路径=os.path.join(os.path.dirname(__file__),'呈现行.module.css')


def 确保样式(文档):
    '呈现行样式只插一次'
    注入模块样式文件(文档,'dsh-present-row',样式路径,样式模块)


def 元素(文档,标签,类名=None):
    '带官方类名和样式模块'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)


def 空切换():
    '准备中的行不能展开'
    return None


def 交付图标(窗口):
    '上游 IconDeliverDocRegular。基础界面组件还没有这个公开函数'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',[
        'M6.15479 4.91687H9.84543',
        'M11.8798 9.55347V2.71525C11.8798 2.37416 11.564 2.09766 11.1744 2.09766H4.82577C4.43618 2.09766 4.12036 2.37416 4.12036 2.71525V9.55347',
        'M2.28735 13.8022V8.84792C2.28735 8.77514 2.36262 8.72673 2.42884 8.75693L13.2936 13.7112C13.3914 13.7558 13.3596 13.9022 13.2521 13.9022H2.38735C2.33213 13.9022 2.28735 13.8575 2.28735 13.8022Z',
        'M7.46929 10.979L13.5783 8.7416C13.6435 8.7177 13.7126 8.76601 13.7126 8.83551L13.7125 13.8022C13.7125 13.8574 13.6678 13.9022 13.6125 13.9022H7.99999',
        'M6.15479 7.2395H9.05644',
    ],16,1)


class 呈现行:
    '一条 present 调用。准备中是静止行，开始后可展开结果'
    def __new__(类,属性):
        '画出这一行并返回根节点'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.展开=False
        return 自身.渲染()

    def 渲染(自身):
        '按阶段画准备行或已开始的行'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            if 属性.get('phase')=='preparing':
                根=元素(文档,'div')
                根.setAttribute('data-tool','present')
                根.setAttribute('data-state','preparing')
                根.setAttribute('aria-label',中文['row.preparing'])
                根.appendChild(披露行({
                    'window':窗口,
                    'title':中文['row.title'],
                    'icon':交付图标(窗口),
                    'open':False,
                    'expandable':False,
                    'onToggle':空切换,
                    'running':True,
                }).渲染())
            else:
                根=自身._已开始(文档,窗口,属性)
            旧=自身.根
            父=None if 旧 is None else 旧.parentNode
            if 旧 is not None and 旧 is not 根:
                if 父 is not None:
                    父.replaceChild(根,旧)
                else:
                    旧.remove()
            自身.根=根
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def _已开始(自身,文档,窗口,属性):
        '记录到的参数和结果。有详情才能展开'
        块=属性.get('block')
        已结算=isinstance(块,dict) and 'kind' in 块
        if not 已结算:
            状态名='running'
            参数原文=块.get('argsRaw') if isinstance(块,dict) else ''
            输出=''
            错误=None
        else:
            错误=块.get('error') if isinstance(块.get('error'),dict) else None
            if isinstance(错误,dict) and 错误.get('code')=='interrupted':
                状态名='stopped'
            elif 块.get('isError'):
                状态名='error'
            else:
                状态名='ok'
            调用=块.get('call') if isinstance(块.get('call'),dict) else None
            参数原文=''
            if 调用 is not None and isinstance(调用.get('argsRaw'),str):
                参数原文=调用['argsRaw']
            elif isinstance(块.get('argsRaw'),str):
                参数原文=块['argsRaw']
            段=[]
            for 项 in 块.get('content') or []:
                if isinstance(项,dict) and 项.get('type')=='text':
                    段.append(项.get('text') or '')
                else:
                    段.append(紧凑json编码(项))
            输出='\n'.join(段)
        if 参数原文 is None:
            参数原文=''
        if 输出:
            详情=输出
        elif 已结算 and isinstance(错误,dict):
            详情=str(错误.get('name') or '')+': '+str(错误.get('code') or '')
        else:
            详情=''
        可展=详情!=''
        打开=自身.展开 and 可展

        def 切换():
            '展开或收起结果'
            自身.展开=not 自身.展开
            自身.渲染()

        摘要=元素(文档,'span','summary')
        状态字=文档.createElement('span')
        状态字.textContent=中文['row.'+状态名]
        路径字=元素(文档,'span','paths')
        路径字.textContent=自身._文件名(参数原文)
        摘要.appendChild(状态字)
        摘要.appendChild(路径字)
        预=元素(文档,'pre','output')
        预.textContent=详情
        子=[]
        子.append(预)
        检视=属性.get('inspect')
        if callable(检视):
            钮=元素(文档,'button','inspect')
            钮.setAttribute('type','button')
            钮.textContent=中文['row.inspect']

            def 点检视(事件,检视=检视):
                '查看这次调用'
                检视()

            钮.addEventListener('click',点检视)
            子.append(钮)
        根=元素(文档,'div')
        根.setAttribute('data-tool','present')
        根.setAttribute('data-state',状态名)
        根.appendChild(披露行({
            'window':窗口,
            'title':中文['row.title'],
            'icon':交付图标(窗口),
            'open':打开,
            'expandable':可展,
            'expandOnRowClick':True,
            'keepContentWhenOpen':True,
            'onToggle':切换,
            'collapsedContent':摘要,
            'children':子,
        }).渲染())
        return 根

    def _文件名(自身,原文):
        '参数还没写完时原样显示。写完则把文件路径用逗号接上'
        try:
            参数=json.loads(原文)
        except Exception:
            return 原文
        if not isinstance(参数,dict) or not isinstance(参数.get('files'),list):
            return 原文
        路径=[]
        for 文件 in 参数['files']:
            if isinstance(文件,dict) and isinstance(文件.get('path'),str):
                路径.append(文件['path'])
        return ', '.join(路径)

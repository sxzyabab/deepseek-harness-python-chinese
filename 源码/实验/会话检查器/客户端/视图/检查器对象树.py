'JSON 详情和惰性运行时对象共用的值树；已登记对象走身份链接'

import json
import math
from nicegui import ui as 界面
from .对象值 import 检查器对象值
from .原始json import 未定义
from .格式 import 失败说明

__all__=['检查器json树','检查器对象树']

页大小=50

def 是对象(值):
    'null、undefined、标量和函数都不是可链接的对象'
    return 值 is not None and 值 is not 未定义 and not isinstance(值,(str,int,float,bool)) and not callable(值)

class 祖先表:
    '按对象身份记住路径；Map 会留住键'
    def __init__(自身,项=()):
        '拷贝已有的身份到路径'
        自身._项=list(项)

    def 获取(自身,对象):
        '这条祖先链上的路径；没有则 None'
        for 已有,路径 in 自身._项:
            if 已有 is 对象:
                return 路径
        return None

    def 设置(自身,对象,路径):
        '记下当前对象'
        自身._项.append((对象,路径))

    def 拷贝(自身):
        '子分支使用新表，避免改到父级'
        return 祖先表(自身._项)

class 值树:
    '根为 $ 的惰性展开树；分支状态跟路径走'
    def __init__(自身):
        '空祖先和按路径记住的展开状态'
        自身.分支态={}
        自身.根祖先=祖先表()
        自身._更新=None
        自身._退订=None

    def 拆除(自身):
        '卸掉对象发布订阅'
        if 自身._退订 is not None:
            自身._退订()
            自身._退订=None
            自身._更新=None

    def 跟上(自身,更新):
        '订阅这一份对象发布；换源时卸掉上一份'
        if 自身._更新 is 更新:
            return
        自身.拆除()
        自身._更新=更新
        def 变了():
            '发布到达后记下修订；下一次渲染读快照'
            return None
        自身._退订=更新.subscribe(变了)

    def _态(自身,路径,根,json模式):
        '首次见到该路径时，根和 JSON 默认展开'
        if 路径 not in 自身.分支态:
            自身.分支态[路径]={'expanded':根 or json模式,'limit':math.inf if json模式 else 页大小,'子祖先':None,'祖先键':None}
        return 自身.分支态[路径]

    def _子祖先(自身,祖先,值,路径,态):
        '把当前值放进子分支的祖先表'
        键=(id(祖先),id(值),路径)
        if 态['祖先键']!=键:
            下一=祖先.拷贝()
            if 是对象(值):
                下一.设置(值,路径)
            态['子祖先']=下一
            态['祖先键']=键
        return 态['子祖先']

    def 分支(自身,属性):
        '一个字段：链接、循环、访问器或缺槽都不再展开'
        值=属性.get('value',未定义)
        名=属性['name']
        路径=属性['path']
        祖先=属性['ancestors']
        根=属性.get('root') is True
        访问器=属性.get('accessor') is True
        缺席=属性.get('absent') is True
        导航=属性.get('navigation')
        翻译=属性['t']
        json模式=导航 is None
        态=自身._态(路径,根,json模式)
        子祖先=自身._子祖先(祖先,值,路径,态)
        try:
            对象表=None if 导航 is None else 导航['objects']
            引用=对象表['reference'](值) if (not 根 and 是对象(值) and 对象表 is not None) else None
            循环=祖先.获取(值) if 是对象(值) else None
            内联=引用 is None or 引用.get('kind')=='nodeData'
            显示=检查器对象值(值) if 内联 and 循环 is None and not 访问器 else None
            条目=[]
            if 态['expanded'] and 显示 is not None and 显示.可展开:
                for 项 in 显示.条目():
                    if json模式 and 项.get('properties'):
                        continue
                    条目.append(项)
                    if len(条目)>态['limit']:
                        break
            内容={'reference':引用,'circular':循环,'display':显示,'entries':条目,'error':None}
        except Exception as 错误:
            内容={'error':失败说明(错误)}
        字段={'type':'span','className':'objectField','text':f'{名}: '}
        if 内容.get('error') is not None:
            return {'type':'li','role':'alert','children':[字段,{'type':'span','text':内容['error']}]}
        if 缺席:
            return {'type':'li','children':[字段,{'type':'span','className':'objectMuted','text':翻译('object.absent')}]}
        if 访问器:
            return {'type':'li','children':[字段,{'type':'span','className':'objectMuted','text':翻译('object.accessor')}]}
        引用=内容.get('reference')
        链接=None
        if 引用 is not None and 导航 is not None:
            def 点链接(事件,引用=引用,导航=导航):
                '打开该引用，不触发展开'
                事件.preventDefault()
                事件.stopPropagation()
                导航['navigate'](引用)
            链接={
                'type':'button',
                'className':'objectReference',
                'text':f"↗ {翻译('object.'+引用['kind'])} · {引用['identity']}",
                'onClick':点链接,
            }
        if 引用 is not None and (引用.get('kind')!='nodeData' or 内容.get('circular') is not None):
            return {'type':'li','children':[字段,链接]}
        if 内容.get('circular') is not None:
            return {'type':'li','children':[字段,{'type':'span','className':'objectMuted','text':f"↩ {内容['circular']}"}]}
        显示=内容['display']
        if not 显示.可展开:
            return {'type':'li','children':[字段,{'type':'span','className':'objectValue','text':显示.标签}]}
        上限=态['limit']
        子项=[]
        if 态['expanded']:
            可见条目=内容['entries'] if 上限==math.inf else 内容['entries'][:上限]
            for 项 in 可见条目:
                属性项=项.get('properties') is True
                子项.append(自身.分支({
                    'value':项.get('value',未定义),
                    'name':翻译('object.properties') if 属性项 else 项['name'],
                    'path':路径 if 属性项 else f"{路径}.{项['name']}",
                    'ancestors':子祖先,
                    'accessor':项.get('accessor') is True,
                    'absent':项.get('absent') is True,
                    'navigation':导航,
                    't':翻译,
                }))
            if len(内容['entries'])==0:
                子项.append({'type':'li','className':'objectMuted','text':翻译('object.empty')})
            if len(内容['entries'])>上限:
                def 再要(路径=路径):
                    '再展开一页'
                    自身.分支态[路径]['limit']+=页大小
                子项.append({'type':'li','children':[{'type':'button','className':'objectReference','text':翻译('object.more'),'onClick':再要}]})
        def 切换(事件,路径=路径):
            '跟 details 的 open 走'
            自身.分支态[路径]['expanded']=事件.currentTarget.open
        return {
            'type':'li',
            'children':[{
                'type':'details',
                'open':态['expanded'],
                'onToggle':切换,
                'summary':{'children':[字段,链接,{'type':'span','className':'objectMuted','text':f" {显示.标签}"}]},
                'list':None if not 态['expanded'] else {'type':'ul','children':子项},
            }],
        }

    def 渲染(自身,属性,换容器=False):
        '从 $ 画出整棵树；换容器时离开上一次的父级'
        自身._上次=属性
        if 换容器:
            自身._根=None
        树={
            'type':'ul',
            'className':'objectTree',
            'cssModule':'检查器.module.css',
            'children':[自身.分支({
                'value':属性.get('value',未定义),
                'name':'$',
                'path':'$',
                'ancestors':自身.根祖先,
                'root':True,
                'navigation':属性.get('navigation'),
                't':属性['t'],
            })],
        }
        自身._铺开(树)
        return 树

    def 重画(自身):
        '展开或翻页后按上次的值再画'
        if getattr(自身,'_上次',None) is not None:
            自身.渲染(自身._上次,换容器=False)

    def _铺开(自身,节点):
        '把值树画成可展开的列表'
        if getattr(自身,'_根',None) is None:
            自身._根=界面.column().classes('objectTree')
        自身._根.clear()
        def 画(项):
            '一个节点'
            if 项 is None:
                return
            if isinstance(项,str):
                if 项!='':
                    界面.label(项)
                return
            if isinstance(项,(list,tuple)):
                for 子 in 项:
                    画(子)
                return
            if not isinstance(项,dict):
                return
            种类=项.get('type') or 'span'
            文=项.get('text') or ''
            点击=项.get('onClick')
            if 种类=='details':
                开=项.get('open') is True
                回调=项.get('onToggle')
                def 切(事件=None,回调=回调,开=开):
                    '翻转 open 再重画'
                    class 目标:
                        '给 onToggle 的 currentTarget'
                        open=not 开
                    class 事件壳:
                        '对齐 currentTarget.open'
                        currentTarget=目标()
                    if callable(回调):
                        回调(事件壳())
                    自身.重画()
                with 界面.column().classes('objectBranch'):
                    with 界面.row():
                        界面.button('▾' if 开 else '▸', on_click=切).props('flat dense')
                        画(项.get('summary'))
                    if 开:
                        画(项.get('list'))
                return
            if 种类=='button':
                def 点(事件=None,点击=点击):
                    '执行后重画'
                    if callable(点击):
                        class 鼠标:
                            '吞掉 preventDefault'
                            def preventDefault(自身):
                                return None
                            def stopPropagation(自身):
                                return None
                        try:
                            点击(鼠标())
                        except TypeError:
                            点击()
                    自身.重画()
                界面.button(文 or ' ', on_click=点).props('flat no-caps dense')
                return
            if 种类 in ('ul','ol','li','div','span','nav'):
                盒=界面.column() if 种类 in ('ul','ol','li','div','nav') else 界面.row()
                类名=项.get('className') or ''
                if 类名:
                    盒.classes(str(类名))
                with 盒:
                    if 文:
                        界面.label(文)
                    画(项.get('children'))
                return
            if 文:
                界面.label(文)
            画(项.get('children'))
        with 自身._根:
            画(节点)

class 检查器json树:
    '序列化后的检查 JSON；容器一开始就展开，没有引用导航'
    def __init__(自身,属性):
        '记下原文和一棵值树'
        自身.属性=属性
        自身._树=值树()
        自身._文本=None
        自身._值=未定义

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '空原文是 undefined；其余按 JSON 解析'
        文本=自身.属性['text']
        if 文本 is not 自身._文本:
            自身._文本=文本
            自身._值=未定义 if 文本=='' else json.loads(文本)
        return 自身._树.渲染({'value':自身._值,'t':自身.属性['t']},换容器=True)

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 检查器对象树:
    '根和嵌套的 Node Data 就地展开；其他已登记对象只给导航链接'
    def __init__(自身,属性):
        '记下对象、导航，并订阅发布'
        自身.属性=属性
        自身._树=值树()
        自身._树.跟上(属性['objects']['updates'])

    def 更新(自身,属性):
        '刷新 props，并在发布源更换时重新订阅'
        自身.属性=属性
        自身._树.跟上(属性['objects']['updates'])

    def 拆除(自身):
        '卸掉发布订阅'
        自身._树.拆除()

    def 渲染(自身):
        '用当前修订画出可导航的值树'
        属性=自身.属性
        更新=属性['objects']['updates']
        自身._树.跟上(更新)
        修订=更新.getSnapshot()
        return 自身._树.渲染({
            'value':属性.get('value',未定义),
            't':属性['t'],
            'navigation':{'objects':属性['objects'],'navigate':属性['navigate'],'revision':修订},
        },换容器=True)

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

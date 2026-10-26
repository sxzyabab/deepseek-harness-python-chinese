'一个版本的详细介绍。相对图片从 Host 上该文档旁边加载'
import os
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.状态点 import 状态点
from .市场存储 import 详情键
from .文案 import 中文句

__all__=['插件详情区','详情文档状态']

样式模块='plugin-detail-section'
失败键={
    'too-large':'detailTooLarge',
    'network':'detailNetwork',
    'denied':'detailDenied',
    'git-unavailable':'detailGitUnavailable',
    'invalid':'detailInvalid',
    'other':'detailFailed',
}

def 详情文档状态(读取):
    '加载中、找到文档、没有文档，或失败'
    if isinstance(读取,dict) and 读取.get('status')=='ready':
        if 读取.get('markdown') is None:
            return {'status':'none'}
        return {'status':'found','markdown':读取['markdown']}
    if isinstance(读取,dict) and 读取.get('status')=='error':
        return 读取
    return {'status':'loading'}

def 确保样式(文档):
    '详情区自己的骨架和滚动区'
    路径=os.path.join(os.path.dirname(__file__),'插件详情区.module.css')
    注入模块样式文件(文档,'插件详情区样式',路径,样式模块)

def 建(文档,标签,类名=None):
    '造一个挂了官方类名的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)

class 插件详情区:
    '按当前语言读详细介绍。没有文档时不占位'
    def __init__(自身,属性):
        '记下请求和读取动作，并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.已请求=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '缺结果时发起读取。失败给出原因和重试'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        请求=属性.get('request') or {}
        def 取语言(快照):
            '当前界面语言'
            if isinstance(快照,dict):
                return 快照.get('active')
            return 快照
        语言=''
        if 'useLocale' in 属性 and 属性['useLocale'] is not None:
            语言=属性['useLocale'](取语言) or ''
        键=详情键(请求,语言)
        def 取详情(表):
            '这一键的读取结果'
            if isinstance(表,dict):
                return 表.get(键)
            return None
        状态=None
        if 'useDetails' in 属性 and 属性['useDetails'] is not None:
            状态=属性['useDetails'](取详情)
        if 自身.已订 is not True:
            def 重画():
                '语言或详情变了就重画'
                自身.渲染()
            if 'useLocale' in 属性 and hasattr(属性.get('useLocale'),'_subscribe'):
                属性['useLocale']._subscribe(重画)
            if 'useDetails' in 属性 and hasattr(属性.get('useDetails'),'_subscribe'):
                属性['useDetails']._subscribe(重画)
            自身.已订=True
        if 状态 is None and 自身.已请求!=键 and 属性.get('loadDetail') is not None:
            自身.已请求=键
            属性['loadDetail'](请求,语言)
        详情=None
        if isinstance(状态,dict) and 状态.get('status')=='ready':
            详情=状态.get('detail')
        文档标识=None
        原文=None
        if isinstance(详情,dict) and 详情.get('status')=='found':
            文档标识=详情.get('document')
            原文=详情.get('markdown')
        if isinstance(状态,dict) and 状态.get('status')=='error':
            展示={'status':'error','message':中文句(失败键.get(状态.get('failure'),'detailFailed'))}
        elif 状态 is None or (isinstance(状态,dict) and 状态.get('status')=='loading'):
            展示={'status':'loading'}
        else:
            展示=详情文档状态({'status':'ready','markdown':原文} if isinstance(详情,dict) else 状态)
        if 展示.get('status')=='none':
            旧=自身.根
            父=None
            if 旧 is not None:
                父=旧.parentNode
                旧.remove()
                自身.根=None
            return None
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        根=建(文档,'section','section')
        根.setAttribute('data-detail-document','')
        if 展示.get('status')=='found':
            区=建(文档,'div','document')
            区.setAttribute('role','region')
            区.setAttribute('aria-label',中文句('detailTitle'))
            区.tabIndex=0
            块=Markdown文本({'window':窗口,'text':展示.get('markdown') or ''}).渲染()
            if 块 is not None:
                区.appendChild(块)
                自身.改图片(块,文档标识,属性.get('detailImage'))
            根.appendChild(区)
        elif 展示.get('status')=='error':
            失败=建(文档,'div','failure')
            警=建(文档,'p','error')
            警.setAttribute('role','alert')
            点=状态点({'window':窗口,'state':'error'}).渲染()
            if 点 is not None:
                警.appendChild(点)
            警.appendChild(文档.createTextNode(展示.get('message') or ''))
            失败.appendChild(警)
            def 重试(事件=None):
                '再读这一份文档'
                if 属性.get('retryDetail') is not None:
                    属性['retryDetail'](请求,语言)
            钮=按钮({
                'window':窗口,'variant':'outline','size':'sm','onClick':重试,'children':中文句('retry'),
            }).渲染()
            if 钮 is not None:
                失败.appendChild(钮)
            根.appendChild(失败)
        else:
            骨架=建(文档,'div','skeleton')
            骨架.setAttribute('role','status')
            骨架.setAttribute('aria-label',中文句('detailLoading'))
            骨架.setAttribute('aria-busy','true')
            骨架.appendChild(建(文档,'span','bar long'))
            骨架.appendChild(建(文档,'span','bar long'))
            骨架.appendChild(建(文档,'span','bar short'))
            根.appendChild(骨架)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根

    def 改图片(自身,块,文档标识,解析):
        '相对图片改成 Host 地址。绝对 http 图片不带引用页'
        if 解析 is None or not hasattr(块,'querySelectorAll'):
            return
        for 图 in 块.querySelectorAll('img'):
            源=图.getAttribute('src')
            if not isinstance(源,str) or 源=='':
                continue
            if 源.startswith('http://') or 源.startswith('https://'):
                图.setAttribute('referrerpolicy','no-referrer')
                continue
            if 文档标识 is None:
                continue
            址=解析(文档标识,源)
            if isinstance(址,str) and 址!='':
                图.setAttribute('src',址)
                图.setAttribute('referrerpolicy','no-referrer')

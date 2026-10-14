from nicegui import ui as 界面
from ...ui_基础界面组件.文件类型图标 import 文件类型图标
from .失败行 import 失败行
from .远程过程调用 import 宿主文件#宿主文件
from .文档.注册表 import 匹配文档预览,二进制文档路径#匹配
from .文档.不可预览 import 不可预览二进制路径#无渲染器二进制
from .文本 import 纯文本体标识#纯文本 id
from .文本.行 import 已载入页,末已载行#行辅助
from .加载指示器 import 加载指示器,加载状态
from .图标 import 不换行图标16,换行图标16#换行字形

__all__=['文本预览','文本预览面板','样式表']
样式表='''
.preview{display:flex;flex:1 1 auto;flex-direction:column;height:100%;min-height:0}
.header{display:flex;flex:0 0 auto;gap:4px;align-items:center;box-sizing:border-box;height:38px;padding:0 6px 0 16px;border-bottom:0.5px solid var(--dsw-alias-border-l3)}
.path{margin-right:12px}
.changed{display:flex;flex:0 0 auto;gap:10px;align-items:center;margin:0;padding:6px 10px;color:var(--dsw-alias-label-secondary);font-size:12px;background:var(--dsw-alias-bg-layer-2);border-bottom:0.5px solid var(--dsw-alias-border-l1)}
.body{position:relative;flex:1 1 auto;min-height:0;margin:0;padding:0;overflow:auto}
'''
界面.add_css(样式表,shared=True)

def _键齐(属性):
    '页签、资源、存储、文案和预览表都在才画'
    if not isinstance(属性,dict):
        return False
    for 键 in ('useTabInfo','useResource','useStore','actions','useDocumentPreviews','t','renderSlot'):
        if 键 not in 属性:
            return False
    return True

def _槽回退(结果,标记):
    '空槽把回退标记原样交回；当选组件已经在构造里画出'
    if isinstance(结果,dict) and 结果.get('type')=='slot-outlet':
        return 结果.get('content') is 标记
    return 结果 is 标记

def 文本预览(
    取标签信息,取资源,取存储,动作,
    加载页,重载页,加载全部,重载全部,
    取文档预览,渲染槽,翻译,
    准备渲染器=None,
):
    '产出迄今所读内容及其控件结构，或进度行'
    标签信息=取标签信息()#标签信息
    标签=标签信息['tab']#标签
    导航=标签['navigation']#导航
    信号=标签['signal'] if 'signal' in 标签 else None#寿命
    元=取资源(标签['contentId'])#元数据快照
    可读=元.get('status')!='none'#可读
    文件=宿主文件(标签['contentId'])#会话文件
    状态=取存储(lambda 总:总['byTab'][标签['id']] if 标签['id'] in 总['byTab'] else None)#桶
    定义列表=取文档预览(lambda 值:值)#定义
    已匹配=匹配文档预览(定义列表,文件['path'])#匹配
    不可预览=不可预览二进制路径(文件['path'])#无认领二进制
    if len(已匹配)>0 and 二进制文档路径(定义列表,文件['path']):#二进制已有渲染器
        候选=list(已匹配)#只用匹配项
    elif len(已匹配)==0 and 不可预览:#无渲染器的二进制
        候选=[]#不回落纯文本
    else:
        兜底=None#纯文本
        for 项 in 定义列表:#找兜底
            if 项.get('id')==纯文本体标识:#纯文本
                兜底=项#记下
                break#停
        候选=list(已匹配)+( [兜底] if 兜底 is not None else [] )#候选
    所选=None#所选
    if 状态 is not None and 'rendererId' in 状态:#有选择
        for 项 in 候选:#找
            if 项.get('id')==状态['rendererId']:#命中
                所选=项#记下
                break#停
    if 所选 is None and len(候选)>0:#自动
        所选=候选[0]#首个
    if 所选 is None and 不可预览:#该格式不能预览
        值=元.get('value')#元数据
        绝对=值['absolutePath'] if isinstance(值,dict) and isinstance(值.get('absolutePath'),str) and 值['absolutePath']!='' else None
        展示=绝对 if 绝对 is not None else 文件['path']#展示路径
        return {#空态
            'kind':'unsupported',
            'path':展示,
            'url':标签['contentId'],
            'message':翻译('unsupportedFile'),
            'fileOwner':{'absolutePath':绝对} if 绝对 is not None else None,
        }#结束
    if 状态 is None or 所选 is None:#尚无
        if 元.get('status')=='none':#无资源
            return {'kind':'status','line':翻译('resourceUnavailable')}#不可用
        启动=None#尚未选定渲染器
        if 所选 is not None and 可读:#可读且已选定
            值=元.get('value')#元数据
            版本=值['version'] if isinstance(值,dict) and 'version' in 值 else None#观察版本
            启动={#首次读取参数
                'mode':所选.get('loading'),
                'tabId':标签['id'],
                'file':文件,
                'signal':信号,
                'version':版本,
                'rendererId':所选['id'],
            }#结束
        return {'kind':'status','loading':加载指示器(翻译('loading')),'start':启动}#加载中
    模式=所选.get('loading')#模式
    当前=状态 if (状态.get('mode') if 'mode' in 状态 else 'text-pages')==模式 else None#当前桶
    页表=当前['pages'] if 当前 is not None and 'pages' in 当前 else {}#页
    已载=已载入页(页表)#有序
    已载至=末已载行(已载)#末行
    有内容=len(已载)>0 or (当前 is not None and 'complete' in 当前 and 当前['complete'] is not None)#有内容
    绝对路径=None#宿主路径
    值=元.get('value')#元数据
    if isinstance(值,dict) and isinstance(值.get('absolutePath'),str) and 值['absolutePath']!='':
        绝对路径=值['absolutePath']#元数据路径
    elif 当前 is not None and isinstance(当前.get('complete'),dict):
        完=当前['complete']#完整结果
        if isinstance(完.get('absolutePath'),str) and 完['absolutePath']!='':
            绝对路径=完['absolutePath']#完整结果路径
    展示路径=绝对路径 if 绝对路径 is not None else 文件['path']#展示路径
    参数=导航['params'] if 'params' in 导航 else None#参数
    行号=参数['line'] if 参数 is not None and 'line' in 参数 else None#行
    观察版本=元['value']['version'] if 元.get('value') is not None and 'version' in 元['value'] else None
    内容=None#文档内容
    if 模式=='bytes-complete':#完整字节
        if 当前 is not None and 'complete' in 当前 and 当前['complete'] is not None:
            内容={'kind':'bytes','data':当前['complete']['data']}#字节
    elif 模式=='renderer' and 当前 is not None:#渲染器自有加载
        修订=当前.get('loadRevision',0)#修订
        def 已载(版本,标识=标签['id'],修订值=修订):
            '渲染器报告这一修订已经画出'
            if 'rendered' in 动作:
                动作['rendered'](标识,修订值,版本)
        def 失败了(标识=标签['id']):
            '渲染器报告这一修订失败'
            if 'failed' in 动作:
                动作['failed'](标识,{'code':'renderer/failed','message':''})
        def 重载渲染器(标识=标签['id'],信号值=信号,渲染器=所选['id'],版本=观察版本):
            '丢掉这一修订再准备渲染器'
            if 准备渲染器 is not None:
                准备渲染器(标识,信号值,渲染器,版本,True)
        内容={'kind':'renderer','revision':修订,'reload':重载渲染器,'failed':失败了,'loaded':已载}
    elif 当前 is not None and len(已载)>0:#文本页
        内容={#文本
            'kind':'text',
            'pages':已载,
            'text':'\n'.join(页['text'] for 页 in 已载 if 页['lines']>0),
            'eof':当前['eof'],
        }#结束
    已变更=(
        当前 is not None and 当前.get('version') is not None and 观察版本 is not None
        and 观察版本!=当前['version'] and 观察版本!=当前.get('observedVersion')
    )#变更
    return {#结构
        'kind':'text-preview',
        'url':标签['contentId'],
        'rendererId':所选['id'],
        'path':展示路径,
        'wrap':状态.get('wrap',True),
        'candidates':[{'id':项['id'],'title':项['title']()} for 项 in 候选],
        'selectedId':所选['id'],
        'selectedTitle':所选['title'](),
        'showWrap':所选.get('wrap') is True,
        'changed':已变更,
        'metaFailure':失败行(翻译,元['failure']) if 元.get('failure') is not None and 有内容 else None,
        'content':内容,
        'hasContent':有内容,
        'failure':失败行(翻译,当前['failure']) if 当前 is not None and 当前.get('failure') is not None else None,
        'failureCode':当前['failure'].get('code') if 当前 is not None and isinstance(当前.get('failure'),dict) else None,
        'fileOwner':{'absolutePath':绝对路径} if isinstance(绝对路径,str) and 绝对路径!='' else None,
        'eof':当前['eof'] if 当前 is not None else True,
        'loading':当前['loading'] if 当前 is not None else False,
        'mode':模式,
        'line':行号,
        'loadedThrough':已载至,
        'labels':{#文案
            'loading':翻译('loading'),
            'loadMore':翻译('loadMore'),
            'changed':翻译('changed'),
            'reloadNow':翻译('reloadNow'),
            'reload':翻译('reload'),
            'openWith':翻译('openWith'),
            'retry':翻译('retry'),
            'wrapEnable':翻译('wrap.enable'),
            'wrapDisable':翻译('wrap.disable'),
            'wrapAria':翻译('wrap.aria'),
            'rendererUnavailable':翻译('rendererUnavailable',{'name':所选['title']()}),
        },
    }#结束


def 空失败出路(代码):
    '空正文失败时的出路：open 交给宿主，none 无动作，retry 再读'
    if 代码 in ('workspace-file/not-text','workspace-file/too-large'):
        return 'open'
    if 代码 in ('workspace-file/not-found','workspace-file/not-regular-file'):
        return 'none'
    return 'retry'


class 文本预览面板:
    '路径、打开方式、换行、重载，以及文档正文或失败空态'

    def __init__(自身,属性):
        '记下标签席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已启动=None
        自身.菜单开=False
        if _键齐(自身.属性):
            自身.渲染()

    def _取(自身,名):
        'props 缺席时返回 None'
        return 自身.属性[名] if 名 in 自身.属性 else None

    def _模型(自身):
        '用面与钩子算出预览结构'
        属性=自身.属性
        取标签=自身._取('useTabInfo')
        取资源=自身._取('useResource')
        取存储=自身._取('useStore')
        动作=自身._取('actions')
        取文档=自身._取('useDocumentPreviews')
        渲染槽=自身._取('renderSlot')
        翻译=自身._取('t')
        if 取标签 is None or 取资源 is None or 取存储 is None or 动作 is None or 取文档 is None or 翻译 is None:
            return None
        return 文本预览(
            取标签,取资源,取存储,动作,
            自身._取('loadPage'),自身._取('reloadPages'),自身._取('loadAll'),自身._取('reloadAll'),
            取文档,渲染槽,翻译,自身._取('prepareRenderer'),
        )

    def _启动(自身,启动):
        '当前尚未读入时按模式读第一页、完整字节或准备渲染器'
        if not isinstance(启动,dict) or 启动.get('mode') is None:
            return
        键=(启动['tabId'],启动['mode'],启动['rendererId'],启动['version'])
        if 自身.已启动==键:
            return
        自身.已启动=键
        模式=启动['mode']
        if 模式=='text-pages':
            读=自身._取('loadPage')
            if 读 is not None:
                读(启动['tabId'],启动['file'],1,启动['signal'],启动['version'])
        elif 模式=='bytes-complete':
            读=自身._取('loadAll')
            if 读 is not None:
                读(启动['tabId'],启动['file'],启动['signal'],启动['version'])
        else:
            准备=自身._取('prepareRenderer')
            if 准备 is not None:
                准备(启动['tabId'],启动['signal'],启动['rendererId'],启动['version'])

    def _标签(自身):
        '当前标签；没有钩子时返回 None'
        取=自身._取('useTabInfo')
        if 取 is None:
            return None
        信息=取()
        return 信息['tab'] if isinstance(信息,dict) else 信息.tab

    def _重载(自身,模型):
        '按当前模式丢掉已读内容再读'
        标签=自身._标签()
        if 标签 is None:
            return
        取资源=自身._取('useResource')
        元=取资源(模型['url']) if 取资源 is not None else {}
        值=元.get('value') if isinstance(元,dict) else None
        版本=值['version'] if isinstance(值,dict) and 'version' in 值 else None
        信号=标签['signal'] if 'signal' in 标签 else None
        文件=宿主文件(标签['contentId'])
        模式=模型.get('mode')
        if 模式=='text-pages':
            重载=自身._取('reloadPages')
            if 重载 is not None:
                重载(标签['id'],文件,信号,版本)
        elif 模式=='bytes-complete':
            重载=自身._取('reloadAll')
            if 重载 is not None:
                重载(标签['id'],文件,信号,版本)
        else:
            准备=自身._取('prepareRenderer')
            if 准备 is not None:
                准备(标签['id'],信号,模型['rendererId'],版本,True)

    def _再读(自身,模型):
        '文本页未结束时读下一页'
        if 模型.get('loading') is True or 模型.get('eof') is True:
            return
        标签=自身._标签()
        读=自身._取('loadPage')
        if 标签 is None or 读 is None:
            return
        取资源=自身._取('useResource')
        元=取资源(模型['url']) if 取资源 is not None else {}
        值=元.get('value') if isinstance(元,dict) else None
        版本=值['version'] if isinstance(值,dict) and 'version' in 值 else None
        信号=标签['signal'] if 'signal' in 标签 else None
        已至=模型['loadedThrough'] if isinstance(模型.get('loadedThrough'),int) else 0
        读(标签['id'],宿主文件(标签['contentId']),已至+1,信号,版本)

    def _画槽(自身,键,拥有方,选项=None):
        '声明过的子槽由宿主画；没有 renderSlot 时跳过'
        渲染槽=自身._取('renderSlot')
        if 渲染槽 is None or 拥有方 is None:
            return None
        return 渲染槽(键,拥有方,选项)

    def 渲染(自身):
        '画出预览头、变更条、正文槽或空态'
        模型=自身._模型()
        if 模型 is None:
            return
        if 模型['kind']=='unsupported':
            with 界面.column().classes('preview'):
                主人=模型['fileOwner'] if 'fileOwner' in 模型 else None
                with 界面.row().classes('header'):
                    界面.label(模型['path']).classes('path')
                    自身._画槽('sidebar.right.tab.document.actions',主人)
                with 界面.column().classes('body'):
                    文件类型图标({'path':模型['path'],'size':36}).渲染()
                    界面.label(模型['message'])
                    自身._画槽('sidebar.right.tab.document.unpreviewable',主人)
            return
        if 模型['kind']=='status':
            自身._启动(模型['start'] if 'start' in 模型 else None)
            with 界面.column().classes('status'):
                if 'line' in 模型 and isinstance(模型['line'],str):
                    界面.label(模型['line'])
                else:
                    加载=模型['loading'] if isinstance(模型.get('loading'),dict) else {}
                    加载状态(加载['label'] if 'label' in 加载 else '').渲染()
            return
        标签文=模型['labels']
        主人=模型['fileOwner'] if 'fileOwner' in 模型 else None
        失败文=模型['failure'] if isinstance(模型.get('failure'),str) and 模型['failure']!='' else None
        元失败=模型['metaFailure'] if isinstance(模型.get('metaFailure'),str) and 模型['metaFailure']!='' else None
        with 界面.column().classes('preview'):
            if 元失败 is not None or 模型.get('changed') is True:
                条文=元失败 if 元失败 is not None else 标签文['changed']
                with 界面.row().classes('changed'):
                    界面.label(条文)
                    界面.button(标签文['reloadNow'], on_click=lambda: 自身._重载(模型)).props('flat dense no-caps')
            with 界面.row().classes('header'):
                界面.label(模型['path']).classes('path')
                候选=模型['candidates'] if isinstance(模型.get('candidates'),list) else []
                if len(候选)>1:
                    def 切换(标识,动作=自身._取('actions')):
                        '记下所选渲染器'
                        标签=自身._标签()
                        if 标签 is not None and 动作 is not None and 'selected' in 动作:
                            动作['selected'](标签['id'],标识)
                    with 界面.button(模型['selectedTitle']).props('flat dense no-caps aria-label="'+标签文['openWith']+'"'):
                        with 界面.menu():
                            for 项 in 候选:
                                界面.menu_item(项['title'], on_click=lambda 标识=项['id']: 切换(标识))
                if 模型.get('showWrap') is True:
                    def 切换换行(动作=自身._取('actions')):
                        '切换换行'
                        标签=自身._标签()
                        if 标签 is not None and 动作 is not None and 'toggledWrap' in 动作:
                            动作['toggledWrap'](标签['id'])
                    换行开=模型.get('wrap') is True
                    提示=标签文['wrapDisable'] if 换行开 else 标签文['wrapEnable']
                    换行钮=界面.button(on_click=切换换行).props(
                        'flat dense round aria-label="'+标签文['wrapAria']+'" title="'+提示+'"'
                    )
                    with 换行钮:
                        if 换行开:
                            不换行图标16(16).渲染()
                        else:
                            换行图标16(16).渲染()
                if 模型.get('content') is not None:
                    自身._画槽('sidebar.right.tab.document.action',{'content':模型['content']},{
                        'entryKey':模型['rendererId'],
                        'hookContext':自身._取('useTabInfo'),
                    })
                界面.button(icon='refresh', on_click=lambda: 自身._重载(模型)).props(
                    'flat dense round aria-label="'+标签文['reload']+'"'
                )
                自身._画槽('sidebar.right.tab.document.actions',主人)
            with 界面.column().classes('body'):
                if 模型.get('mode')!='renderer' and 模型.get('hasContent') is not True and 失败文 is None:
                    加载状态(标签文['loading']).渲染()
                if 模型.get('content') is not None:
                    回退标记=object()
                    画出=自身._画槽('sidebar.right.tab.document',{
                        'resourceAddress':模型['url'],
                        'content':模型['content'],
                        'wrap':模型.get('wrap') is True,
                        'addResource':自身._取('addResource'),
                        'setResources':自身._取('setResources'),
                    },{
                        'entryKey':模型['rendererId'],
                        'hookContext':自身._取('useTabInfo'),
                        'fallback':回退标记,
                    })
                    if 画出 is None or _槽回退(画出,回退标记):
                        界面.label(标签文['rendererUnavailable']).classes('statusLine')
                if 失败文 is not None:
                    if 模型.get('hasContent') is True:
                        with 界面.row():
                            界面.label(失败文)
                            界面.button(标签文['retry'], on_click=lambda: 自身._再读(模型)).props('flat dense no-caps')
                    else:
                        with 界面.column().classes('empty'):
                            文件类型图标({'path':模型['path'],'size':36}).渲染()
                            界面.label(失败文)
                            出路=空失败出路(模型.get('failureCode'))
                            if 出路=='open':
                                自身._画槽('sidebar.right.tab.document.unpreviewable',主人)
                            elif 出路=='retry':
                                界面.button(标签文['retry'], on_click=lambda: 自身._重载(模型)).props('flat dense no-caps')
                if 模型.get('mode')=='text-pages' and 模型.get('hasContent') is True and 模型.get('eof') is not True and 失败文 is None:
                    if 模型.get('loading') is True:
                        加载状态(标签文['loading'],行内=True).渲染()
                    else:
                        界面.button(标签文['loadMore'], on_click=lambda: 自身._再读(模型)).props('flat dense no-caps')

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
            自身.已启动=None
            自身.菜单开=False
        return 自身.渲染()

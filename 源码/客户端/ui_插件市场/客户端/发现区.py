'发现：搜索一个插件索引，打开条目，确认后安装'
import os
import threading
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import (
    图标下箭头描边常规,
    图标加号16,
    图标垃圾桶16,
    图标检索16,
    图标刷新16,
    图标警告16,
)
from ...ui_基础界面组件.插件画稿 import 插件画稿默认
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.标签 import 标签
from ...ui_基础界面组件.模态 import 模态
from ...ui_基础界面组件.状态点 import 状态点
from ...ui_基础界面组件.胶囊 import 胶囊
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.输入 import 输入
from .插件详情区 import 插件详情区
from .文案 import 中文句
from .呈现 import 可安装,格式日期,呈现版本,来源事实,索引标签,显示声明,条目标题,带文本

__all__=['发现区']

样式模块='discover-section'
文本延迟秒=0.25
图标边=36
失败键={'fetch':'readFailed','invalid':'readInvalid','changed':'readChanged'}
事实键={
    'package':'factPackage','registry':'factRegistry','repository':'factRepository',
    'commit':'factCommit','directory':'factDirectory',
}

def 确保样式(文档):
    '把发现页样式模块插进文档'
    注入模块样式文件(
        文档,
        '发现区样式',
        os.path.join(os.path.dirname(__file__),'发现区.module.css'),
        样式模块,
    )

def 建(文档,标签名,类名=None):
    '造一个挂了官方类名的节点'
    节点=文档.createElement(标签名)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)

def 画图标(窗口,工厂,尺寸=None):
    '按边长画一枚已有图标'
    属性={'window':窗口}
    if 尺寸 is not None:
        属性['size']=尺寸
    return 工厂(属性)

def 文字钮(窗口,属性,图标工厂=None,图标尺寸=None):
    '先画按钮，再把图标插到文字前面'
    绘制=dict(属性)
    绘制['window']=窗口
    节点=按钮(绘制).渲染()
    if 节点 is not None and 图标工厂 is not None:
        图=画图标(窗口,图标工厂,图标尺寸)
        if 图 is not None:
            if 节点.firstChild is None:
                节点.appendChild(图)
            else:
                节点.insertBefore(图,节点.firstChild)
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

def 源失败文案(失败):
    '保存索引源被拒绝时的中文句'
    种类=None if not isinstance(失败,dict) else 失败.get('kind')
    if 种类=='invalid':
        return 中文句('sourceInvalid')
    if 种类=='duplicate':
        return 中文句('sourceDuplicate')
    if 种类=='unavailable':
        return 中文句('sourceUnavailable')
    return 中文句('sourceFailed')

def 排序菜单标识(排序):
    '排序菜单里的标识'
    if 排序.get('kind')=='key':
        return 'key:'+str(排序.get('id'))
    return 排序.get('kind')

def 未筛选(查询):
    '没有字、分类和标签'
    if 查询 is None:
        return True
    return 查询.get('text','').strip()=='' and 查询.get('category') is None and len(查询.get('labels') or [])==0

def 市场图标(文档,窗口,地址,尺寸,失败地址):
    '图标加载失败时用默认画稿'
    if not isinstance(地址,str) or 地址=='' or 地址==失败地址:
        图=插件画稿默认({'window':窗口,'size':尺寸}).渲染()
        return 图,失败地址
    图=文档.createElement('img')
    图.className='image'
    标样式模块(图,样式模块)
    图.setAttribute('src',地址)
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('alt','')
    图.setAttribute('loading','lazy')
    图.setAttribute('referrerpolicy','no-referrer')
    return 图,失败地址

class 发现区:
    '插件页的发现标签：工具栏、列表、条目页，以及索引源和安装确认'
    def __init__(自身,属性):
        '记下注入面，并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.已确保=False
        自身.确认=None
        自身.文本=''
        自身.菜单=None
        自身.已打开=None
        自身.列表网址=None
        自身.图标失败={}
        自身.文本定时=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '空闲和读取中是骨架。没有索引源是空状态。其余画出浏览器'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        def 取状态(快照):
            '整份发现状态'
            return 快照
        def 取语言(快照):
            '当前界面语言'
            if isinstance(快照,dict):
                return 快照.get('active')
            return 快照
        状态=属性['useDiscover'](取状态) if 'useDiscover' in 属性 else None
        语言=属性['useLocale'](取语言) if 'useLocale' in 属性 else ''
        if 自身.已订 is not True:
            def 重画():
                '状态变了就重画'
                自身.渲染()
            for 钩名 in ('useDiscover','useLocale','useDetails'):
                钩=属性.get(钩名)
                if 钩 is not None and hasattr(钩,'_subscribe'):
                    钩._subscribe(重画)
            自身.已订=True
        if 自身.已确保 is not True and 属性.get('ensure') is not None:
            自身.已确保=True
            属性['ensure']()
        if not isinstance(状态,dict):
            状态={'status':'idle','indexes':[],'listing':None,'editing':False,'draft':'','saving':False,'sourceFailure':None}
        面=属性
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        根=建(文档,'div','section')
        根.setAttribute('data-plugin-tab','discover')
        态=状态.get('status')
        if 态 in ('idle','loading'):
            根.appendChild(自身.列表骨架(文档,中文句('loading')))
        elif 态=='error':
            根.appendChild(自身.失败行(文档,窗口,中文句('sourcesFailed'),属性.get('reload')))
        elif 状态.get('listing') is None:
            根.appendChild(自身.空状态(文档,窗口,属性))
        else:
            列表=状态['listing']
            if 自身.列表网址!=列表.get('url'):
                自身.列表网址=列表.get('url')
                自身.文本=(列表.get('query') or {}).get('text') or ''
                自身.菜单=None
                自身.已打开=None
            根.appendChild(自身.画浏览(文档,窗口,状态,列表,面,语言 or ''))
        源框=自身.索引源对话框(文档,窗口,状态,面)
        if 源框 is not None:
            根.appendChild(源框)
        确认框=自身.确认对话框(文档,窗口,面)
        if 确认框 is not None:
            根.appendChild(确认框)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根

    def 列表骨架(自身,文档,标签文):
        '四行卡片骨架'
        列=建(文档,'ul','cards')
        列.setAttribute('role','status')
        列.setAttribute('aria-label',标签文)
        列.setAttribute('aria-busy','true')
        序号=0
        while 序号<4:
            项=建(文档,'li','card')
            项.setAttribute('aria-hidden','true')
            项.appendChild(建(文档,'span','icon skeletonFill'))
            主=建(文档,'div','main')
            主.appendChild(建(文档,'span','skeletonBar skeletonTitle skeletonFill'))
            主.appendChild(建(文档,'span','skeletonBar skeletonDescription skeletonFill'))
            项.appendChild(主)
            列.appendChild(项)
            序号=序号+1
        return 列

    def 失败行(自身,文档,窗口,文句,重试):
        '一句失败和重试'
        行=建(文档,'div','failure')
        警=建(文档,'p','error')
        警.setAttribute('role','alert')
        点=状态点({'window':窗口,'state':'error'}).渲染()
        if 点 is not None:
            警.appendChild(点)
        警.appendChild(文档.createTextNode(文句))
        行.appendChild(警)
        钮=文字钮(窗口,{
            'variant':'outline','size':'sm','onClick':重试,'children':中文句('retry'),
        })
        if 钮 is not None:
            行.appendChild(钮)
        return 行

    def 空状态(自身,文档,窗口,属性):
        '还没有索引源'
        盒=建(文档,'div','empty')
        图=插件画稿默认({'window':窗口,'size':48}).渲染()
        if 图 is not None:
            盒.appendChild(图)
        题=建(文档,'p','emptyTitle')
        题.textContent=中文句('emptyTitle')
        盒.appendChild(题)
        述=建(文档,'p','muted')
        述.textContent=中文句('emptyDescription')
        盒.appendChild(述)
        钮=文字钮(窗口,{
            'variant':'primary','size':'sm','onClick':属性.get('toggleSources'),'children':中文句('addFirstSource'),
        },图标加号16,13)
        if 钮 is not None:
            盒.appendChild(钮)
        return 盒

    def 画浏览(自身,文档,窗口,状态,列表,面,语言):
        '工具栏和列表。打开条目时换成条目页'
        查询=列表.get('query') or {}
        值=列表.get('value')
        打开=自身.已打开
        当前条目=None
        if 打开 is not None and isinstance(值,dict):
            for 条目 in 值.get('entries') or []:
                if 条目.get('name')==打开.get('name'):
                    当前条目=条目
                    break
            if 当前条目 is None:
                当前条目=打开
        盒=文档.createElement('div')
        if 当前条目 is not None and isinstance(值,dict):
            盒.appendChild(自身.条目详情(文档,窗口,当前条目,值,面,语言))
            return 盒
        声明=自身.声明(值,面,语言)
        选中={'url':列表.get('url')}
        for 索引 in 状态.get('indexes') or []:
            if 索引.get('url')==列表.get('url'):
                选中=索引
        市场名=索引标签(选中,面['resolveText'])
        排序=查询.get('sort') or {'kind':'index'}
        排序项=[]
        if (查询.get('text') or '').strip()!='':
            排序项.append({'id':'relevance','label':中文句('sortRelevance')})
        排序项.append({'id':'index','label':中文句('sortDefault')})
        排序项.append({'id':'published','label':中文句('sortPublished')})
        for 项 in 声明['sortKeys']:
            排序项.append({'id':'key:'+项['id'],'label':项['title']})
        排序名=中文句('sortDefault')
        标识=排序菜单标识(排序)
        for 项 in 排序项:
            if 项['id']==标识:
                排序名=项['label']
        有方向=排序.get('kind') in ('published','key')
        忙=列表.get('status')=='loading' and 值 is not None
        具=建(文档,'div','toolbar')
        具.appendChild(自身.市场菜单(文档,窗口,状态,列表,面,市场名))
        搜索=输入({
            'window':窗口,'className':'search','type':'search','value':自身.文本,
            'placeholder':中文句('search'),'onChange':自身.改文本,
        }).渲染()
        if 搜索 is not None:
            标样式模块(搜索,样式模块)
            框=搜索.querySelector('input') if hasattr(搜索,'querySelector') else None
            if 框 is not None:
                框.setAttribute('aria-label',中文句('search'))
                框.type='search'
            图=画图标(窗口,图标检索16,14)
            if 图 is not None:
                搜索.insertBefore(图,搜索.firstChild)
            具.appendChild(搜索)
        if len(声明['labels'])>0:
            具.appendChild(自身.标签菜单(文档,窗口,查询,声明,面))
        具.appendChild(自身.排序菜单(文档,窗口,查询,排序,排序项,排序名,有方向,面))
        刷新图=状态点({'window':窗口,'state':'ongoing'}) if 忙 else None
        刷新钮=文字钮(窗口,{
            'variant':'ghost','size':'sm','onClick':面.get('refresh'),
            'disabled':列表.get('status')=='loading',
        },None if 忙 else 图标刷新16,14)
        if 忙 and 刷新钮 is not None and 刷新图 is not None:
            点=刷新图.渲染()
            if 点 is not None:
                if 刷新钮.firstChild is None:
                    刷新钮.appendChild(点)
                else:
                    刷新钮.insertBefore(点,刷新钮.firstChild)
        if 刷新钮 is not None:
            刷新钮.setAttribute('aria-label',中文句('refresh'))
            泡=提示泡({
                'window':窗口,'label':中文句('refresh'),'side':'bottom','portal':True,
                'delayMs':500,'focusDelayMs':500,'children':刷新钮,
            }).渲染()
            具.appendChild(泡 if 泡 is not None else 刷新钮)
        盒.appendChild(具)
        if len(声明['categories'])>0:
            盒.appendChild(自身.分类行(文档,窗口,查询,声明,面))
        if 列表.get('failure') is not None:
            盒.appendChild(自身.失败行(文档,窗口,中文句(失败键.get(列表.get('failure'),'readFailed')),面.get('retry')))
        if 值 is None:
            if 列表.get('status')=='loading':
                盒.appendChild(自身.列表骨架(文档,中文句('loading')))
        elif 值.get('total')==0:
            句=建(文档,'p','muted')
            句.textContent=中文句('emptyIndex' if 未筛选(列表.get('answered')) else 'noMatches')
            盒.appendChild(句)
        else:
            列=建(文档,'ul','cards')
            if 忙:
                列.setAttribute('aria-busy','true')
            for 条目 in 值.get('entries') or []:
                列.appendChild(自身.条目卡片(文档,窗口,条目,面,语言,声明['labels']))
            盒.appendChild(列)
            if 值.get('nextOffset') is not None:
                更多=文字钮(窗口,{
                    'variant':'outline','size':'sm','className':'more',
                    'disabled':列表.get('status')!='ready','onClick':面.get('more'),
                    'children':中文句('showMore'),
                })
                if 更多 is not None:
                    盒.appendChild(更多)
        return 盒

    def 声明(自身,值,面,语言):
        '分类、标签和排序键按标题排列'
        if not isinstance(值,dict):
            return {'categories':[],'labels':[],'sortKeys':[]}
        元=值.get('metadata') or {}
        return {
            'categories':显示声明(元.get('categories') or {},面['resolveText'],语言),
            'labels':显示声明(元.get('labels') or {},面['resolveText'],语言),
            'sortKeys':显示声明(元.get('sortKeys') or {},面['resolveText'],语言),
        }

    def 改文本(自身,文字):
        '停输入后再把查询交给控制器'
        自身.文本=文字
        if 自身.文本定时 is not None:
            自身.文本定时.cancel()
        属性=自身.属性
        def 到点():
            '把当前字写进查询'
            状态=None
            if 'useDiscover' in 属性:
                def 取(快照):
                    '整份状态'
                    return 快照
                状态=属性['useDiscover'](取)
            列表=None if not isinstance(状态,dict) else 状态.get('listing')
            if 列表 is None or 属性.get('search') is None:
                return
            属性['search'](带文本(列表.get('query') or {},自身.文本))
        自身.文本定时=threading.Timer(文本延迟秒,到点)
        自身.文本定时.daemon=True
        自身.文本定时.start()

    def 切菜单(自身,菜单名):
        '同时只开一个菜单'
        自身.菜单=None if 自身.菜单==菜单名 else 菜单名
        自身.渲染()

    def 点市场(自身,事件=None):
        '打开或关上索引菜单'
        自身.切菜单('market')

    def 点标签(自身,事件=None):
        '打开或关上标签菜单'
        自身.切菜单('filter')

    def 点排序(自身,事件=None):
        '打开或关上排序菜单'
        自身.切菜单('sort')

    def 关菜单(自身,事件=None):
        '点外面或选中后关掉。已经关着就不再画'
        if 自身.菜单 is None:
            return
        自身.菜单=None
        自身.渲染()

    def 市场菜单(自身,文档,窗口,状态,列表,面,市场名):
        '切换索引。最后一项打开索引源'
        条目=[]
        for 索引 in 状态.get('indexes') or []:
            条目.append({'id':索引['url'],'label':索引标签(索引,面['resolveText'])})
        def 选(标识):
            '管理或切换'
            自身.菜单=None
            if 标识=='manage':
                if 面.get('toggleSources') is not None:
                    面['toggleSources']()
            elif 面.get('select') is not None:
                面['select'](标识)
        锚=文字钮(窗口,{
            'variant':'ghost','size':'sm','className':'marketButton',
            'onClick':自身.点市场,'children':市场名,
        },None,None)
        if 锚 is not None:
            名=文档.createElement('span')
            名.className='marketName'
            标样式模块(名,样式模块)
            名.textContent=市场名
            while 锚.firstChild is not None:
                锚.firstChild.remove()
            锚.appendChild(名)
            箭=画图标(窗口,图标下箭头描边常规,12)
            if 箭 is not None:
                箭.setAttribute('aria-hidden','true')
                锚.appendChild(箭)
            锚.setAttribute('aria-haspopup','menu')
            锚.setAttribute('aria-expanded','true' if 自身.菜单=='market' else 'false')
            锚.setAttribute('aria-label',中文句('marketMenu',{'market':市场名}))
        return 菜单({
            'window':窗口,'open':自身.菜单=='market','onClose':自身.关菜单,
            'portal':True,'selectedId':列表.get('url'),'items':条目,
            'footer':[{'id':'manage','label':中文句('manageSources')}],
            'onSelect':选,'anchor':锚,
        }).渲染()

    def 标签菜单(自身,文档,窗口,查询,声明,面):
        '标签可多选'
        条目=[{'id':项['id'],'label':项['title']} for 项 in 声明['labels']]
        已选=list(查询.get('labels') or [])
        def 选(标识):
            '点一下加上，再点去掉'
            下一=[]
            见过=False
            for 项 in 已选:
                if 项==标识:
                    见过=True
                else:
                    下一.append(项)
            if 见过 is not True:
                下一.append(标识)
            查询下一=dict(查询)
            查询下一['labels']=下一
            if 面.get('search') is not None:
                面['search'](查询下一)
        文=中文句('filter') if len(已选)==0 else 中文句('filterCount',{'count':str(len(已选))})
        锚=文字钮(窗口,{
            'variant':'ghost','size':'sm','onClick':自身.点标签,'children':文,
        })
        if 锚 is not None:
            锚.setAttribute('aria-haspopup','menu')
            锚.setAttribute('aria-expanded','true' if 自身.菜单=='filter' else 'false')
        return 菜单({
            'window':窗口,'open':自身.菜单=='filter',
            'onClose':自身.关菜单,
            'portal':True,'align':'end','selectedIds':已选,'items':条目,'onSelect':选,'anchor':锚,
        }).渲染()

    def 排序菜单(自身,文档,窗口,查询,排序,排序项,排序名,有方向,面):
        '选择排序。有方向时脚部可以反过来'
        def 选(标识):
            '写成下一次查询的排序'
            自身.菜单=None
            if 标识=='direction' and 有方向:
                下一=dict(排序)
                下一['direction']='desc' if 排序.get('direction')=='asc' else 'asc'
                查询下一=dict(查询)
                查询下一['sort']=下一
                if 面.get('search') is not None:
                    面['search'](查询下一)
                return
            if 标识 in ('index','relevance'):
                查询下一=dict(查询)
                查询下一['sort']={'kind':标识}
                if 面.get('search') is not None:
                    面['search'](查询下一)
                return
            if 标识=='published':
                查询下一=dict(查询)
                查询下一['sort']={'kind':'published','direction':'desc'}
                if 面.get('search') is not None:
                    面['search'](查询下一)
                return
            for 项 in 排序项:
                if 项['id']==标识 and 标识.startswith('key:'):
                    声明=None
                    元标识=标识[4:]
                    状态=自身.属性
                    列表=None
                    if 'useDiscover' in 状态:
                        def 取(快照):
                            '整份状态'
                            return 快照
                        快照=状态['useDiscover'](取)
                        if isinstance(快照,dict):
                            列表=快照.get('listing')
                    值=None if not isinstance(列表,dict) else 列表.get('value')
                    键表=((值 or {}).get('metadata') or {}).get('sortKeys') or {}
                    声明=键表.get(元标识)
                    if isinstance(声明,dict):
                        查询下一=dict(查询)
                        查询下一['sort']={'kind':'key','id':元标识,'direction':声明.get('order')}
                        if 面.get('search') is not None:
                            面['search'](查询下一)
        脚=None
        if 有方向:
            脚文=中文句('switchToDescending' if 排序.get('direction')=='asc' else 'switchToAscending')
            脚=[{'id':'direction','label':脚文}]
        锚=文字钮(窗口,{
            'variant':'ghost','size':'sm','onClick':自身.点排序,
            'children':中文句('sortBy',{'sort':排序名}),
        })
        if 锚 is not None:
            箭=画图标(窗口,图标下箭头描边常规,12)
            if 箭 is not None:
                箭.setAttribute('aria-hidden','true')
                锚.appendChild(箭)
            锚.setAttribute('aria-haspopup','menu')
            锚.setAttribute('aria-expanded','true' if 自身.菜单=='sort' else 'false')
        绘制={
            'window':窗口,'open':自身.菜单=='sort',
            'onClose':自身.关菜单,
            'portal':True,'align':'end','selectedId':排序菜单标识(排序),
            'items':排序项,'onSelect':选,'anchor':锚,
        }
        if 脚 is not None:
            绘制['footer']=脚
        return 菜单(绘制).渲染()

    def 分类行(自身,文档,窗口,查询,声明,面):
        '全部在前，其余按声明顺序'
        行=建(文档,'div','categories')
        行.setAttribute('role','group')
        行.setAttribute('aria-label',中文句('categoriesLabel'))
        def 选全部(事件=None):
            '清掉分类'
            查询下一=dict(查询)
            查询下一['category']=None
            if 面.get('search') is not None:
                面['search'](查询下一)
        全部=胶囊({
            'window':窗口,'active':查询.get('category') is None,'onClick':选全部,'children':中文句('allCategories'),
        }).渲染()
        if 全部 is not None:
            全部.setAttribute('aria-pressed','true' if 查询.get('category') is None else 'false')
            行.appendChild(全部)
        for 项 in 声明['categories']:
            标识=项['id']
            def 选类(事件=None,标识=标识):
                '换成这个分类'
                查询下一=dict(查询)
                查询下一['category']=标识
                if 面.get('search') is not None:
                    面['search'](查询下一)
            片=胶囊({
                'window':窗口,'active':查询.get('category')==标识,'onClick':选类,'children':项['title'],
            }).渲染()
            if 片 is not None:
                片.setAttribute('aria-pressed','true' if 查询.get('category')==标识 else 'false')
                行.appendChild(片)
        return 行

    def 条目卡片(自身,文档,窗口,条目,面,语言,标签列):
        '图标、标题、标签、一句说明，以及唯一的动作'
        标题=条目标题(条目,面)
        版本=呈现版本(条目)
        日期=格式日期(版本.get('publishTimestamp') or 0,语言,'medium')
        项=建(文档,'li','card')
        项.setAttribute('data-market-entry',条目.get('name') or '')
        图盒=建(文档,'span','icon')
        图盒.setAttribute('aria-hidden','true')
        图,失败=市场图标(文档,窗口,条目.get('icon'),图标边,自身.图标失败.get(条目.get('name')))
        if 图 is not None:
            名=条目.get('name')
            def 失败了(事件=None,名=名,地址=条目.get('icon')):
                '记下失败的地址，下次用默认画稿'
                自身.图标失败[名]=地址
                自身.渲染()
            if hasattr(图,'addEventListener'):
                图.addEventListener('error',失败了)
            图盒.appendChild(图)
        项.appendChild(图盒)
        主=建(文档,'div','main')
        题行=建(文档,'div','titleRow')
        def 打开(事件=None):
            '打开这个条目'
            自身.已打开=条目
            自身.渲染()
        开=文档.createElement('button')
        开.type='button'
        开.className='cardOpen'
        标样式模块(开,样式模块)
        开.setAttribute('aria-label',中文句('openEntry',{'name':标题}))
        开.textContent=标题
        开.addEventListener('click',打开)
        题行.appendChild(开)
        for 标签项 in 标签列:
            if 标签项['id'] in (条目.get('metadata') or {}).get('labels') or []:
                签=标签({'window':窗口,'children':标签项['title']}).渲染()
                if 签 is not None:
                    题行.appendChild(签)
        主.appendChild(题行)
        if 条目.get('description') is not None:
            述=建(文档,'span','description')
            述.textContent=面['resolveText'](条目['description'])
            主.appendChild(述)
        元=建(文档,'span','meta')
        if 条目.get('author') is None:
            元.textContent=中文句('entryMeta',{'version':版本.get('version'),'date':日期})
        else:
            元.textContent=中文句('entryMetaAuthor',{
                'version':版本.get('version'),'author':条目.get('author'),'date':日期,
            })
        主.appendChild(元)
        项.appendChild(主)
        尾=建(文档,'div','cardEnd')
        动作=自身.条目动作(文档,窗口,条目,标题,面)
        if 动作 is not None:
            尾.appendChild(动作)
        项.appendChild(尾)
        return 项

    def 条目动作(自身,文档,窗口,条目,标题,面):
        '未安装且可装则安装。否则打开已安装'
        安装态=(条目.get('installation') or {}).get('status')
        if 安装态!='not-installed':
            键='statusInstalled'
            if 安装态=='update-available':
                键='statusUpdate'
            elif 安装态=='provided':
                键='statusProvided'
            def 打开已装(事件=None):
                '切到已安装并打开这个包'
                if 自身.属性.get('openPackage') is not None:
                    自身.属性['openPackage'](条目.get('name'))
            钮=文字钮(窗口,{
                'variant':'ghost','size':'sm','onClick':打开已装,'children':中文句(键),
            })
            if 钮 is not None:
                钮.setAttribute('aria-label',中文句('openInstalled',{'name':标题}))
            return 钮
        版本=呈现版本(条目)
        兼容=版本.get('compatibility') or {}
        if 可安装(兼容) is not True:
            钮=文字钮(窗口,{
                'variant':'outline','size':'sm','className':'blocked','children':中文句('install'),
            })
            if 钮 is not None:
                钮.setAttribute('aria-disabled','true')
                钮.setAttribute('aria-label',中文句('installTitle',{'name':标题}))
            泡=提示泡({
                'window':窗口,
                'label':中文句('noCompatibleVersion',{'runtime':兼容.get('runtimeVersion')}),
                'side':'bottom','portal':True,'delayMs':300,'children':钮,
            }).渲染()
            return 泡 if 泡 is not None else 钮
        def 安装(事件=None):
            '打开确认，安装默认版本'
            自身.确认={'entry':条目,'version':版本}
            自身.渲染()
        钮=文字钮(窗口,{
            'variant':'outline','size':'sm','onClick':安装,'children':中文句('install'),
        })
        if 钮 is not None:
            钮.setAttribute('aria-label',中文句('installTitle',{'name':标题}))
        return 钮

    def 条目详情(自身,文档,窗口,条目,列表值,面,语言):
        '返回、简介、详细介绍、版本和来源'
        标题=条目标题(条目,面)
        版本=呈现版本(条目)
        日期=格式日期(版本.get('publishTimestamp') or 0,语言,'long')
        根=建(文档,'div','detail')
        根.setAttribute('data-market-detail',条目.get('name') or '')
        def 返回(事件=None):
            '回到列表，查询保持不变'
            自身.已打开=None
            自身.渲染()
        屑=建(文档,'button','crumb')
        屑.type='button'
        箭=画图标(窗口,图标下箭头描边常规,None)
        if 箭 is not None:
            箭.classList.add('crumbIcon')
            标样式模块(箭,样式模块)
            箭.setAttribute('aria-hidden','true')
            屑.appendChild(箭)
        屑字=文档.createElement('span')
        屑字.textContent=中文句('backToList')
        屑.appendChild(屑字)
        屑.addEventListener('click',返回)
        根.appendChild(屑)
        头=建(文档,'div','detailHead')
        图盒=建(文档,'span','icon')
        图盒.setAttribute('aria-hidden','true')
        图,失败=市场图标(文档,窗口,条目.get('icon'),图标边,自身.图标失败.get(条目.get('name')))
        if 图 is not None:
            图盒.appendChild(图)
        头.appendChild(图盒)
        主=建(文档,'div','main')
        题行=建(文档,'div','titleRow')
        题=建(文档,'h3','detailTitle')
        题.textContent=标题
        题行.appendChild(题)
        签=标签({'window':窗口,'tone':'neutral','children':版本.get('version') or ''}).渲染()
        if 签 is not None:
            题行.appendChild(签)
        主.appendChild(题行)
        if 标题!=条目.get('name'):
            元=建(文档,'span','meta')
            元.textContent=条目.get('name') or ''
            主.appendChild(元)
        头.appendChild(主)
        动作=自身.条目动作(文档,窗口,条目,标题,面)
        if 动作 is not None:
            头.appendChild(动作)
        根.appendChild(头)
        if 条目.get('description') is not None:
            述=建(文档,'p','detailDescription')
            述.textContent=面['resolveText'](条目['description'])
            根.appendChild(述)
        兼容=版本.get('compatibility') or {}
        if 兼容.get('compatible') is not True:
            根.appendChild(自身.注意(文档,窗口,自身.兼容句(兼容)))
        详情盒=建(文档,'div','detailDocument')
        请求={
            'url':列表值.get('url'),'name':条目.get('name'),'version':版本.get('version'),
            'npm':(版本.get('source') or {}).get('type')=='npm',
        }
        详情=插件详情区({
            'window':窗口,'request':请求,'loadDetail':面.get('loadDetail'),'retryDetail':面.get('retryDetail'),
            'detailImage':面.get('detailImage'),'useDetails':自身.属性.get('useDetails'),
            'useLocale':自身.属性.get('useLocale'),
        }).渲染()
        if 详情 is not None:
            详情盒.appendChild(详情)
        根.appendChild(详情盒)
        版本区=建(文档,'section','detailSection')
        版本题=建(文档,'h4','sectionTitle')
        版本题.textContent=中文句('versionsTitle')
        版本区.appendChild(版本题)
        版本列=建(文档,'ul','versions')
        版本列.setAttribute('aria-label',中文句('versionsLabel',{'name':标题}))
        for 项 in 条目.get('versions') or []:
            版本列.appendChild(自身.版本行(文档,窗口,条目,项,标题,语言))
        版本区.appendChild(版本列)
        根.appendChild(版本区)
        来源区=建(文档,'section','detailSection')
        来源题=建(文档,'h4','sectionTitle')
        来源题.textContent=中文句('factSource')
        来源区.appendChild(来源题)
        表=建(文档,'dl','facts')
        if 条目.get('author') is not None:
            表.appendChild(自身.事实(文档,中文句('factAuthor'),条目.get('author')))
        if 条目.get('homepage') is not None:
            表.appendChild(自身.链接事实(文档,中文句('factHomepage'),条目.get('homepage'),None))
        仓库=条目.get('repository')
        if isinstance(仓库,dict):
            表.appendChild(自身.链接事实(文档,中文句('factSourceCode'),仓库.get('url'),仓库.get('directory')))
        for 事实 in 来源事实(条目.get('name') or '',版本):
            表.appendChild(自身.代码事实(文档,中文句(事实键[事实['kind']]),事实['value']))
        表.appendChild(自身.事实(文档,中文句('factPublished'),日期))
        分类标识=(条目.get('metadata') or {}).get('category')
        分类=None if 分类标识 is None else (列表值.get('metadata') or {}).get('categories',{}).get(分类标识)
        if isinstance(分类,dict):
            表.appendChild(自身.事实(文档,中文句('factCategory'),面['resolveText'](分类.get('title'))))
        标签声明=显示声明((列表值.get('metadata') or {}).get('labels') or {},面['resolveText'],语言)
        命中=[]
        for 标签项 in 标签声明:
            if 标签项['id'] in (条目.get('metadata') or {}).get('labels') or []:
                命中.append(标签项)
        if len(命中)>0:
            行=文档.createElement('div')
            名=文档.createElement('dt')
            名.textContent=中文句('factLabels')
            值格=建(文档,'dd','tags')
            for 标签项 in 命中:
                签=标签({'window':窗口,'children':标签项['title']}).渲染()
                if 签 is not None:
                    值格.appendChild(签)
            行.appendChild(名)
            行.appendChild(值格)
            表.appendChild(行)
        表.appendChild(自身.事实(文档,中文句('factMarket'),面['resolveText'](列表值.get('title'))))
        来源区.appendChild(表)
        根.appendChild(来源区)
        return 根

    def 兼容句(自身,兼容):
        '豁免或版本范围'
        if 兼容.get('exempted') is True:
            return 中文句('exempted')
        需求=兼容.get('requirements') or {}
        范围=' '.join(str(项) for 项 in 需求.values())
        return 中文句('incompatible',{'runtime':兼容.get('runtimeVersion'),'range':范围})

    def 注意(自身,文档,窗口,文句):
        '带警告图标的提示'
        段=建(文档,'p','notice')
        段.setAttribute('role','note')
        图=画图标(窗口,图标警告16,14)
        if 图 is not None:
            图.setAttribute('aria-hidden','true')
            段.appendChild(图)
        字=文档.createElement('span')
        字.textContent=文句
        段.appendChild(字)
        return 段

    def 版本行(自身,文档,窗口,条目,版本,标题,语言):
        '版本上的状态标签。可安装且不是随附包时给出安装'
        当前=(条目.get('installation') or {}).get('installedVersion')==版本.get('version')
        提供=(条目.get('installation') or {}).get('status')=='provided'
        兼容=版本.get('compatibility') or {}
        可给=当前 is not True and 提供 is not True and 可安装(兼容)
        项=建(文档,'li','versionRow')
        项.setAttribute('data-market-version',版本.get('version') or '')
        主=建(文档,'div','main')
        题行=建(文档,'div','titleRow')
        强=建(文档,'span','strong')
        强.textContent=版本.get('version') or ''
        题行.appendChild(强)
        if 版本.get('version')==条目.get('defaultVersion'):
            签=标签({'window':窗口,'tone':'info','children':中文句('versionDefault')}).渲染()
            if 签 is not None:
                题行.appendChild(签)
        主体=(版本.get('version') or '').split('+',1)[0]
        if '-' in 主体:
            签=标签({'window':窗口,'tone':'neutral','children':中文句('versionPrerelease')}).渲染()
            if 签 is not None:
                题行.appendChild(签)
        if 当前:
            签=标签({'window':窗口,'tone':'success','children':中文句('versionInstalled')}).渲染()
            if 签 is not None:
                题行.appendChild(签)
        if 兼容.get('compatible') is not True:
            键='versionExempted' if 兼容.get('exempted') is True else 'versionIncompatible'
            签=标签({'window':窗口,'tone':'warning','children':中文句(键)}).渲染()
            if 签 is not None:
                题行.appendChild(签)
        主.appendChild(题行)
        元=建(文档,'span','meta')
        if 兼容.get('compatible') is True:
            元.textContent=格式日期(版本.get('publishTimestamp') or 0,语言,'medium')
        else:
            元.textContent=自身.兼容句(兼容)
        主.appendChild(元)
        项.appendChild(主)
        if 可给:
            def 安装(事件=None,版本=版本):
                '确认安装这一版'
                自身.确认={'entry':条目,'version':版本}
                自身.渲染()
            钮=文字钮(窗口,{
                'variant':'ghost','size':'sm','onClick':安装,'children':中文句('install'),
            })
            if 钮 is not None:
                钮.setAttribute('aria-label',中文句('installVersionTitle',{'name':标题,'version':版本.get('version')}))
                项.appendChild(钮)
        return 项

    def 事实(自身,文档,名文,值文):
        '一行名称和值'
        行=文档.createElement('div')
        名=文档.createElement('dt')
        名.textContent=名文
        值=文档.createElement('dd')
        值.textContent='' if 值文 is None else str(值文)
        行.appendChild(名)
        行.appendChild(值)
        return 行

    def 代码事实(自身,文档,名文,值文):
        '值放在 code 里'
        行=文档.createElement('div')
        名=文档.createElement('dt')
        名.textContent=名文
        值=文档.createElement('dd')
        码=文档.createElement('code')
        码.textContent='' if 值文 is None else str(值文)
        值.appendChild(码)
        行.appendChild(名)
        行.appendChild(值)
        return 行

    def 链接事实(自身,文档,名文,网址,目录):
        '新标签打开。仓库可以带目录'
        行=文档.createElement('div')
        名=文档.createElement('dt')
        名.textContent=名文
        值=文档.createElement('dd')
        链=文档.createElement('a')
        链.className='link'
        标样式模块(链,样式模块)
        链.setAttribute('href',网址 or '')
        链.setAttribute('target','_blank')
        链.setAttribute('rel','noopener noreferrer')
        链.textContent=网址 or ''
        值.appendChild(链)
        if 目录 is not None:
            值.appendChild(文档.createTextNode(' '))
            码=文档.createElement('code')
            码.textContent=str(目录)
            值.appendChild(码)
        行.appendChild(名)
        行.appendChild(值)
        return 行

    def 索引源对话框(自身,文档,窗口,状态,面):
        '列出索引源，并添加新的地址'
        if 状态.get('editing') is not True:
            return None
        体=建(文档,'div','dialogBody')
        if len(状态.get('indexes') or [])>0:
            列=建(文档,'ul','sourceList')
            列.setAttribute('aria-label',中文句('sourcesLabel'))
            for 索引 in 状态.get('indexes') or []:
                列.appendChild(自身.索引源行(文档,窗口,索引,状态,面))
            体.appendChild(列)
        表单=建(文档,'form','sourceForm')
        def 提交(事件=None):
            '不走浏览器提交'
            if 事件 is not None and hasattr(事件,'preventDefault'):
                事件.preventDefault()
            if 面.get('addSource') is not None:
                面['addSource']()
        表单.addEventListener('submit',提交)
        框=输入({
            'window':窗口,'className':'grow','value':状态.get('draft') or '',
            'placeholder':中文句('sourcePlaceholder'),'onChange':面.get('editDraft'),
        }).渲染()
        if 框 is not None:
            标样式模块(框,样式模块)
            输入框=框.querySelector('input') if hasattr(框,'querySelector') else None
            if 输入框 is not None:
                输入框.setAttribute('aria-label',中文句('sourceUrl'))
                if 状态.get('sourceFailure') is not None:
                    输入框.setAttribute('aria-invalid','true')
                输入框.setAttribute('data-modal-autofocus','')
            表单.appendChild(框)
        加=文字钮(窗口,{
            'variant':'primary','size':'sm',
            'disabled':状态.get('saving') is True or (状态.get('draft') or '').strip()=='',
            'onClick':面.get('addSource'),'children':中文句('addSource'),
        },图标加号16,13)
        if 加 is not None:
            加.setAttribute('type','submit')
            表单.appendChild(加)
        体.appendChild(表单)
        if 状态.get('sourceFailure') is not None:
            警=建(文档,'p','error')
            警.setAttribute('role','alert')
            警.textContent=源失败文案(状态.get('sourceFailure'))
            体.appendChild(警)
        体.appendChild(自身.注意(文档,窗口,中文句('sourcesTrust')))
        框体=模态({
            'window':窗口,'open':True,'onClose':面.get('toggleSources'),
            'title':中文句('sourcesTitle'),'closeLabel':中文句('close'),
            'description':中文句('sourcesDescription'),'className':'dialog','children':体,
        }).渲染()
        if 框体 is not None and hasattr(框体,'querySelector'):
            卡=框体.querySelector('.模态')
            if 卡 is not None:
                标样式模块(卡,样式模块)
        return 框体

    def 索引源行(自身,文档,窗口,索引,状态,面):
        '标题、地址、错误和移除'
        项=建(文档,'li','sourceRow')
        主=建(文档,'div','main')
        强=建(文档,'span','strong')
        强.textContent=索引标签(索引,面['resolveText'])
        主.appendChild(强)
        元=建(文档,'span','meta')
        元.textContent=索引.get('url') or ''
        主.appendChild(元)
        if 索引.get('error') is not None:
            错=建(文档,'span','sourceError')
            错.textContent=str(索引.get('error'))
            主.appendChild(错)
        项.appendChild(主)
        网址=索引.get('url')
        def 移除(事件=None,网址=网址):
            '去掉这个索引源'
            if 面.get('removeSource') is not None:
                面['removeSource'](网址)
        钮=文字钮(窗口,{
            'variant':'ghost','size':'sm','disabled':状态.get('saving') is True,'onClick':移除,'children':'',
        },图标垃圾桶16,13)
        if 钮 is not None:
            钮.setAttribute('aria-label',中文句('removeSourceNamed',{'url':网址}))
            泡=提示泡({
                'window':窗口,'label':中文句('removeSource'),'side':'bottom','portal':True,
                'delayMs':300,'children':钮,
            }).渲染()
            项.appendChild(泡 if 泡 is not None else 钮)
        return 项

    def 确认对话框(自身,文档,窗口,面):
        '确认后把精确安装目标交给插件页'
        选择=自身.确认
        if 选择 is None:
            return None
        条目=选择['entry']
        版本=选择['version']
        标题=条目标题(条目,面)
        体=建(文档,'div','dialogBody')
        头=建(文档,'div','confirmHead')
        图盒=建(文档,'span','icon')
        图盒.setAttribute('aria-hidden','true')
        图,失败=市场图标(文档,窗口,条目.get('icon'),图标边,自身.图标失败.get(条目.get('name')))
        if 图 is not None:
            图盒.appendChild(图)
        头.appendChild(图盒)
        主=建(文档,'div','main')
        强=建(文档,'span','strong')
        强.textContent=标题
        主.appendChild(强)
        元=建(文档,'span','meta')
        元.textContent=版本.get('version') or ''
        主.appendChild(元)
        头.appendChild(主)
        体.appendChild(头)
        表=建(文档,'dl','facts')
        if 条目.get('author') is not None:
            表.appendChild(自身.事实(文档,中文句('factAuthor'),条目.get('author')))
        for 事实 in 来源事实(条目.get('name') or '',版本):
            表.appendChild(自身.代码事实(文档,中文句(事实键[事实['kind']]),事实['value']))
        体.appendChild(表)
        兼容=版本.get('compatibility') or {}
        if 兼容.get('compatible') is not True:
            体.appendChild(自身.注意(文档,窗口,中文句('exempted')))
        体.appendChild(自身.注意(文档,窗口,中文句('installTrust')))
        def 取消(事件=None):
            '关上确认'
            自身.确认=None
            自身.渲染()
        def 确定(事件=None):
            '把安装目标交给拥有者'
            自身.确认=None
            目标=dict(版本.get('install') or {})
            目标['title']=标题
            目标['version']=版本.get('version')
            if 自身.属性.get('install') is not None:
                自身.属性['install'](目标)
            自身.渲染()
        取消钮=文字钮(窗口,{'variant':'outline','onClick':取消,'children':中文句('cancel')})
        确定钮=文字钮(窗口,{'variant':'primary','onClick':确定,'children':中文句('install')})
        脚=[]
        if 取消钮 is not None:
            脚.append(取消钮)
        if 确定钮 is not None:
            脚.append(确定钮)
        框体=模态({
            'window':窗口,'open':True,'onClose':取消,'title':中文句('confirmTitle',{'name':标题}),
            'closeLabel':中文句('close'),'className':'dialog','children':体,'footer':脚,
        }).渲染()
        if 框体 is not None and hasattr(框体,'querySelector'):
            卡=框体.querySelector('.模态')
            if 卡 is not None:
                标样式模块(卡,样式模块)
        return 框体

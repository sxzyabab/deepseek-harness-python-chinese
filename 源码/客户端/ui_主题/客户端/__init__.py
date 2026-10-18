from ...模块.客户端.通告 import 取握手窗口
import json
import os
from ...存储 import 声明存储
from ..主题设置 import (
    主题设置命名空间,主题偏好表,默认偏好,默认字号表,字体角色,字号规格,字体族字段,主题偏好字段,
    字体族变量,是否字号,规范化字体族,
)
from ..异常 import 主题错误
from . import 文案,外观行,字号行,字体族行,字体设置组
from .文案 import 设置命名空间,中文,英文

__all__=[
    '依赖','应用','文案','外观行','字号行','字体族行','字体设置组',
    '设置命名空间','主题运行时',
]

依赖=['slots','locale','remote','configForms']

内置主题=(
    {'id':'light','colorScheme':'light','tokens':{}},
    {'id':'dark','colorScheme':'dark','tokens':{}},
)
内置检视令牌=(
    {'name':'--dsw-alias-bg-base','description':'Application base background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-bg-base'},
    {'name':'--dsw-alias-bg-layer-1','description':'Primary raised surface background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-bg-layer-1'},
    {'name':'--dsw-alias-bg-layer-2','description':'Secondary nested surface background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-bg-layer-2'},
    {'name':'--dsw-alias-bg-overlay','description':'Overlay and popover background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-bg-overlay'},
    {'name':'--dsw-alias-border-l1','description':'Primary subtle border.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-border-l1'},
    {'name':'--dsw-alias-border-l2','description':'Secondary stronger border.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-border-l2'},
    {'name':'--dsw-alias-brand-primary','description':'Primary brand accent.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-brand-primary'},
    {'name':'--dsw-alias-label-primary','description':'Primary text color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-label-primary'},
    {'name':'--dsw-alias-label-secondary','description':'Secondary text color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-label-secondary'},
    {'name':'--dsw-alias-state-error-primary','description':'Primary error state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-error-primary'},
    {'name':'--dsw-alias-state-idle-primary','description':'Primary inactive state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-idle-primary'},
    {'name':'--dsw-alias-state-success-primary','description':'Primary success state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-success-primary'},
    {'name':'--dsw-alias-state-warn-primary','description':'Primary warning state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-warn-primary'},
    {'name':'--dsw-specific-sidebar-fill','description':'Sidebar column and title-row background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-specific-sidebar-fill'},
)

def 动态令牌(名):
    '当前组合里多出来的令牌'
    项={
        'name':名,
        'description':'Theme token registered by the current Client composition.',
        'valueType':'CSS value',
        'requiresLightAndDark':True,
    }
    if 名.startswith('--'):
        项['cssVariable']=名
    return 项

class 主题运行时:
    'light/dark 内置。读取走取主题，偏好写入走设主题，连续变化走 theme/change'
    def __init__(自身,上下文,宿主):
        '记下上下文和设置作用域，并读启动脚本已经写在 body 上的字号和字体'
        自身.上下文=上下文
        自身.宿主=宿主
        自身.主题列表=list(内置主题)
        自身.偏好=默认偏好
        自身.修订=0
        自身.在途写入=0
        自身.覆盖层={}
        自身.覆盖序号=0
        窗口=取握手窗口()
        文档=窗口.document
        def 读字号(角色):
            'body 上的整数 px；越界就用该角色缺省'
            原文=文档.body.style.getPropertyValue(字号规格[角色]['variable'])
            缓冲=''
            for 字 in 原文.strip():
                if 字.isdigit() or (字=='-' and 缓冲==''):
                    缓冲+=字
                    continue
                break
            数字=None
            if 缓冲 not in ('','-'):
                数字=int(缓冲)
            if 数字 is None or not 是否字号(角色,数字):
                return 字号规格[角色]['default']
            return 数字
        自身.字号表={
            'text':读字号('text'),
            'code':读字号('code'),
            'terminal':读字号('terminal'),
        }
        体样式=文档.body.style
        自身.字体族表={
            'text':规范化字体族(体样式.getPropertyValue(字体族变量('text'))),
            'code':规范化字体族(体样式.getPropertyValue(字体族变量('code'))),
            'terminal':规范化字体族(体样式.getPropertyValue(字体族变量('terminal'))),
        }
        自身.媒体=窗口.matchMedia('(prefers-color-scheme: dark)')
        自身.快照=自身.编快照()
        if 自身.媒体 is not None:
            媒体=自身.媒体
            def 色板变了(事件=None):
                '偏好为 system 时重发'
                if 自身.偏好!='system':
                    return
                自身.发布()
            def 挂色板():
                '系统色板变化时重发'
                媒体.addEventListener('change',色板变了)
                def 拆():
                    '卸下系统色板监听'
                    媒体.removeEventListener('change',色板变了)
                return 拆
            上下文.副作用(挂色板,'ui-theme: prefers-color-scheme listener')
        def 挂采纳():
            '设置作用域变化时采纳'
            def 采纳变更():
                '不写回'
                自身.采纳()
            return 宿主.subscribe(采纳变更)
        上下文.副作用(挂采纳,'ui-theme: settings scope adoption')
        自身.采纳()
        def 装字号快捷键(范围):
            '桌面壳才登记正文字号增减，步进作用于三个角色'
            if 范围.shortcuts.runtime!='desktop':
                return
            组合=[]
            for 方向,键码,增量 in (('increase','Equal',1),('decrease','Minus',-1)):
                绑定={'code':键码,'modifiers':['primary']}
                if 方向=='increase':
                    绑定表=[绑定,{'code':键码,'modifiers':['primary','shift']}]
                else:
                    绑定表=[绑定]
                for 候选 in 绑定表:
                    组合.append({
                        'binding':范围.shortcuts.describeBinding(候选)['binding'],
                        'delta':增量,
                    })
                def 标签(方向=方向):
                    '快捷键标签用正文字号的中文原文'
                    return 中文['fontSize.text.'+方向]
                def 登记固定(方向=方向,绑定=绑定,绑定表=绑定表,标签=标签):
                    '登记这一方向的固定快捷键'
                    return 范围.shortcuts.registerFixed({
                        'id':'fontSize.'+方向,
                        'label':标签,
                        'keys':范围.shortcuts.describeBinding(绑定)['keys'],
                        'bindings':绑定表,
                        'group':'application',
                    })
                范围.副作用(登记固定,'ui-theme: '+方向+' font size reference')
            def 看输入(输入):
                '匹配字号快捷键并步进'
                if 输入['type']=='reset':
                    return
                手势=输入['gesture']
                情境=输入['context']
                if 手势['composing'] or 手势['defaultPrevented'] or 手势['repeat'] or 情境['region']=='terminal':
                    return
                命中=None
                for 项 in 组合:
                    项绑定=项['binding']
                    if 项绑定['code']!=手势['code']:
                        continue
                    相符=True
                    for 修饰 in ('control','alt','shift','meta'):
                        if 手势[修饰]!=(修饰 in 项绑定['modifiers']):
                            相符=False
                            break
                    if 相符:
                        命中=项
                        break
                if 命中 is None:
                    return
                输入['consume']()
                自身.调整字号(命中['delta'])
            def 挂输入():
                '监听固定快捷键'
                return 范围.shortcuts.observeFixedInput(看输入)
            范围.副作用(挂输入,'ui-theme: font size input')
        上下文.依赖启动(['shortcuts','locale'],装字号快捷键)

    def 取主题(自身):
        '当前快照。下次变化前保持同一引用'
        return 自身.快照

    def 导出检视令牌(自身):
        '不读 DOM，导出可 JSON 化的令牌目录'
        令牌表={}
        for 项 in 内置检视令牌:
            令牌表[项['name']]=项
        for 主题 in 自身.主题列表:
            for 名 in 主题['tokens']:
                if 名 not in 令牌表:
                    令牌表[名]=动态令牌(名)
        for 层 in 自身.覆盖层.values():
            for 名 in 层['tokens']:
                if 名 not in 令牌表:
                    令牌表[名]=动态令牌(名)
        结果=[dict(项) for 项 in 令牌表.values()]
        def 按名(项):
            '按令牌名排序'
            return 项['name']
        结果.sort(key=按名)
        return 结果

    def 设主题(自身,标识):
        '未知 id 抛错。内置偏好写入设置作用域'
        已登记=False
        for 主题 in 自身.主题列表:
            if 主题['id']==标识:
                已登记=True
                break
        if 标识!='system' and not 已登记:
            raise 主题错误('theme "'+标识+'" is not registered')
        if 自身.偏好==标识:
            return
        自身.偏好=标识
        if 标识 in 主题偏好表:
            def 写偏好():
                '写入偏好字段'
                return 自身.宿主.set(主题偏好字段,标识)
            自身.写入(写偏好)
        自身.发布()

    def 设字号(自身,角色,像素):
        '改一个角色的字号。越界抛错。没变则不写'
        规格=字号规格[角色]
        if not 是否字号(角色,像素):
            raise 主题错误(角色+' font size '+str(像素)+' is outside '+str(规格['min'])+'..'+str(规格['max']))
        if 自身.字号表[角色]==像素:
            return
        下一=dict(自身.字号表)
        下一[角色]=像素
        自身.字号表=下一
        def 写():
            '写入该字号字段'
            return 自身.宿主.set(规格['field'],像素)
        自身.写入(写)
        自身.发布()

    def 调整字号(自身,增量):
        '各角色在自己的范围内步进，有变化才一次写入并发一次 theme/change'
        字号表=dict(自身.字号表)
        字段表={}
        for 角色 in 字体角色:
            规格=字号规格[角色]
            像素=max(规格['min'],min(规格['max'],字号表[角色]+增量))
            if 像素==字号表[角色]:
                continue
            字号表[角色]=像素
            字段表[规格['field']]=像素
        if len(字段表)==0:
            return
        自身.字号表=字号表
        操作表=[{'op':'set','path':[字段],'value':值} for 字段,值 in 字段表.items()]
        def 写():
            '一次写入全部变化的字号'
            return 自身.宿主.mutate(操作表)
        自身.写入(写)
        自身.发布()

    def 设字体族(自身,角色,值):
        '规范化后写入。规范化结果没变则不写'
        列表=规范化字体族(值)
        if 自身.字体族表[角色]==列表:
            return
        下一=dict(自身.字体族表)
        下一[角色]=列表
        自身.字体族表=下一
        def 写():
            '写入该字体字段'
            return 自身.宿主.set(字体族字段[角色],列表)
        自身.写入(写)
        自身.发布()

    def 写入(自身,操作):
        '排队一次设置写入，落定且没有自己的写入在途时再采纳'
        自身.在途写入+=1
        def 收尾(*位置参数):
            '这次写入结束后采纳持久分区'
            自身.在途写入-=1
            自身.采纳()
        操作().最终(收尾)

    def 采纳(自身):
        '没有自己的写入在途时，采纳作用域里已接受的分区'
        if 自身.在途写入>0:
            return
        分区=自身.宿主.getSnapshot()['value']
        if 分区 is None:
            return
        字号表={
            'text':分区['fontSize'],
            'code':分区['codeFontSize'],
            'terminal':分区['terminalFontSize'],
        }
        字体族表={
            'text':规范化字体族(分区['textFontFamily']),
            'code':规范化字体族(分区['codeFontFamily']),
            'terminal':规范化字体族(分区['terminalFontFamily']),
        }
        相同=自身.偏好==分区['preference']
        if 相同:
            for 角色 in 字体角色:
                if 自身.字号表[角色]!=字号表[角色] or 自身.字体族表[角色]!=字体族表[角色]:
                    相同=False
                    break
        if 相同:
            return
        自身.偏好=分区['preference']
        自身.字号表=字号表
        自身.字体族表=字体族表
        自身.发布()

    def 登记(自身,定义):
        '登记主题。system 或重复 id 抛错。返回只拆这一次登记的拆除器'
        if 定义['id']=='system':
            raise 主题错误('"system" is a preference, not a registrable theme id')
        for 已有 in 自身.主题列表:
            if 已有['id']==定义['id']:
                raise 主题错误('theme "'+定义['id']+'" is already registered')
        自身.主题列表=[*自身.主题列表,定义]
        自身.发布()
        def 拆除():
            '卸下该主题。若正被选中则回到默认偏好'
            还在=False
            for 已有 in 自身.主题列表:
                if 已有['id']==定义['id']:
                    还在=True
                    break
            if not 还在:
                return
            自身.主题列表=[已有 for 已有 in 自身.主题列表 if 已有['id']!=定义['id']]
            if 自身.偏好==定义['id']:
                自身.偏好=默认偏好
            自身.发布()
        return 拆除

    def 覆盖令牌(自身,来源,令牌表):
        '叠一层覆盖。同来源再调会整层替换并压到最上'
        已校验={}
        for 名,值 in 令牌表.items():
            if isinstance(值,str):
                raise TypeError(
                    'theme override "'+名+'" from "'+来源+'" is a bare string — pass { light: '
                    +json.dumps(值)+', dark: '+json.dumps(值)+' } '
                    +'(repeat the value when it is the same in both palettes); a single value goes illegible when the user switches color scheme'
                )
            if not isinstance(值,dict) or not isinstance(值.get('light'),str) or not isinstance(值.get('dark'),str):
                raise TypeError(
                    'theme override "'+名+'" from "'+来源+'" must map to a { light, dark } pair of strings — one value per color scheme'
                )
            已校验[名]={'light':值['light'],'dark':值['dark']}
        层={'seq':自身.覆盖序号,'tokens':已校验}
        自身.覆盖序号+=1
        自身.覆盖层[来源]=层
        自身.发布()
        def 拆除():
            '只拆这一层；来源已换层则不动'
            if 自身.覆盖层.get(来源) is not 层:
                return
            del 自身.覆盖层[来源]
            自身.发布()
        return 拆除

    def 编快照(自身):
        '按偏好解析活动主题，并叠上覆盖层'
        if 自身.偏好=='system':
            解析标识='dark' if 自身.媒体 is not None and 自身.媒体.matches is True else 'light'
        else:
            解析标识=自身.偏好
        活动=None
        for 主题 in 自身.主题列表:
            if 主题['id']==解析标识:
                活动=主题
                break
        if 活动 is None:
            raise 主题错误('theme registry lost "'+解析标识+'"')
        return {
            'preference':自身.偏好,
            'fontSizes':自身.字号表,
            'fontFamilies':自身.字体族表,
            'active':自身.组合活动(活动),
            'themes':list(自身.主题列表),
            'revision':自身.修订,
        }

    def 组合活动(自身,活动):
        '无覆盖层则原样返回；有层则按序号后层胜出，并按当前色板取值'
        if len(自身.覆盖层)==0:
            return 活动
        令牌=dict(活动['tokens'])
        层表=list(自身.覆盖层.values())
        def 按序号(层):
            '覆盖层序号'
            return 层['seq']
        层表.sort(key=按序号)
        for 层 in 层表:
            for 名,模式 in 层['tokens'].items():
                令牌[名]=模式[活动['colorScheme']]
        活动副本=dict(活动)
        活动副本['tokens']=令牌
        return 活动副本

    def 发布(自身):
        '递增修订并广播 theme/change'
        自身.修订+=1
        自身.快照=自身.编快照()
        自身.上下文.广播('theme/change',自身.快照)

def 应用(上下文,配置=None):
    '提供 theme 服务，并登记通用区的外观行和字体设置'
    窗口=取握手窗口()
    文档=窗口.document
    if 文档 is not None:
        插件标识='@deepseek-ai/dsh-client-ui-theme'
        样式目录=os.path.join(os.path.dirname(__file__),'..','样式')
        样式表=(
            ('base.css','基线.css'),
            ('corner-shape.css','角形态.css'),
            ('design-platform.css','设计平台.css'),
            ('focus.css','聚焦.css'),
            ('onboarding.css','上手引导.css'),
            ('scrollbar.css','滚动条.css'),
            ('gradient-shadow-text.css','渐变阴影.css'),
            ('shiki.css','代码高亮.css'),
        )
        for 原名,中文名 in 样式表:
            def 挂(原名=原名,中文名=中文名):
                '把这一张全局样式挂进 head，拆插件时摘掉'
                标签=文档.createElement('style')
                标签.setAttribute('data-plugin',插件标识)
                标签.setAttribute('data-plugin-css',插件标识+'/'+原名)
                句柄=open(os.path.join(样式目录,中文名),encoding='utf-8')
                标签.textContent=句柄.read()
                句柄.close()
                文档.head.appendChild(标签)
                def 拆():
                    '摘掉这张样式'
                    标签.remove()
                return 拆
            上下文.副作用(挂,'ui-theme: '+原名+' stylesheet')
    def 登记词典():
        '登记外观和字体的中英文案表'
        return 上下文.locale.register(设置命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-theme: settings row dictionaries')
    宿主=上下文.configForms.get(主题设置命名空间)
    主题=主题运行时(上下文,宿主)
    上下文.提供服务('theme',主题)
    def 初始外观():
        '默认跟随系统，修订 -1，好让修订 0 算一次变化'
        return {'preference':'system','revision':-1}
    def 同步外观(草稿,偏好,修订):
        '修订不大于当前则丢弃'
        if 修订<=草稿['revision']:
            return
        草稿['preference']=偏好
        草稿['revision']=修订
    外观存储=声明存储({'init':初始外观,'actions':{'sync':同步外观}})
    def 初始字体():
        '缺省字号、空字体列表、修订 -1'
        return {
            'fontSizes':{
                'text':默认字号表['text'],
                'code':默认字号表['code'],
                'terminal':默认字号表['terminal'],
            },
            'fontFamilies':{'text':'','code':'','terminal':''},
            'revision':-1,
        }
    def 同步字体(草稿,字号表,字体族表,修订):
        '修订不大于当前则丢弃'
        if 修订<=草稿['revision']:
            return
        草稿['fontSizes']=字号表
        草稿['fontFamilies']=字体族表
        草稿['revision']=修订
    字体存储=声明存储({'init':初始字体,'actions':{'sync':同步字体}})
    已烤={'外观':None,'字体':None}
    def 同步(快照):
        '把快照写进已经烤上的行存储'
        if 已烤['外观'] is not None:
            已烤['外观']['sync'](快照['preference'],快照['revision'])
        if 已烤['字体'] is not None:
            已烤['字体']['sync'](快照['fontSizes'],快照['fontFamilies'],快照['revision'])
    上下文.监听('theme/change',同步)
    def 注入外观(动作):
        '记下外观行动作并补当前快照'
        已烤['外观']=动作
        同步(主题.取主题())
        def 写入主题(标识):
            '写入偏好'
            主题.设主题(标识)
        return {'setTheme':写入主题}
    def 登记外观():
        '登记通用区外观行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'appearance',
            'order':10,
            'store':外观存储,
            'locale':设置命名空间,
            'inject':注入外观,
        },外观行.外观行)
    上下文.slots.inject('settings.general.item',登记外观)
    def 注入字体(动作):
        '记下字体行动作并补当前快照'
        已烤['字体']=动作
        同步(主题.取主题())
        def 写入字体(角色,值):
            '写入该角色的字体列表'
            主题.设字体族(角色,值)
        def 写入字号(角色,像素):
            '写入该角色的字号'
            主题.设字号(角色,像素)
        return {'setFontFamily':写入字体,'setFontSize':写入字号}
    def 登记字体():
        '登记通用区字体设置'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'font-size',
            'order':11,
            'store':字体存储,
            'locale':设置命名空间,
            'inject':注入字体,
        },字体设置组.字体设置组)
    上下文.slots.inject('settings.general.item',登记字体)

inject=依赖
apply=应用

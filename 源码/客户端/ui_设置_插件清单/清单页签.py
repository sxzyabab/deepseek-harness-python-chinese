from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标下chevron14,图标检索16
from ..ui_基础界面组件.状态点 import 状态点,样式表 as 点样式
from ..ui_基础界面组件.菜单 import 菜单
from .异常 import 插件清单错误,页面失败文案

__all__=['插件清单错误','插件清单页签','阶段文案键','模块短名','条目匹配']#仅中文公开名

阶段文案键={#fiber 阶段 → 文案键
    'pending':'pending',#等待依赖
    'loading':'loadingPhase',#加载中
    'active':'active',#已挂载
    'failed':'failed',#挂载失败
    'unloading':'unloading',#卸载中
}#阶段键结束

阶段点态={#带点的阶段
    'pending':'idle',#等待
    'loading':'ongoing',#加载
    'unloading':'ongoing',#卸载
}#阶段点结束

标签调={#偏离默认启用的色调
    'disabled':'neutral',#停用
    'conditional':'warning',#条件
    'preset':'info',#预设提供
    'failed':'danger',#失败
}#色调结束

骨架格=(0,1,2,3)#读取中占位卡

样式表='''
.section{container:plugin-inventory / inline-size;display:flex;flex-direction:column;gap:14px;width:100%;max-width:760px;color:var(--dsw-alias-label-primary)}
.status,.failure p{margin:0}
.status,.failure{font-size:13px;line-height:20px;color:var(--dsw-alias-label-tertiary)}
.failure{display:flex;flex-direction:column;align-items:flex-start;gap:8px;color:var(--dsw-alias-state-error-primary)}
.statusWithDot{display:inline-flex;align-items:center;gap:6px}
button.failureButton{border:0.5px solid var(--dsw-alias-border-l3);border-radius:var(--dsw-radius-sm);padding:4px 10px;background:transparent;color:var(--dsw-alias-label-primary);font:inherit;cursor:pointer}
.catalog{display:flex;flex-direction:column;gap:12px}
.search{position:relative;display:flex;align-items:center;width:100%;color:var(--dsw-alias-label-tertiary)}
.search .searchIcon{position:absolute;left:12px;pointer-events:none;z-index:1}
.search .searchInput{width:100%}
.search .searchInput .q-field__control{height:36px;min-height:36px;padding:0 12px 0 36px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1);box-shadow:none}
.search .searchInput .q-field__control:before,.search .searchInput .q-field__control:after{display:none}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0;padding:0;list-style:none}
.card{display:flex;flex-direction:column;min-width:0;overflow:hidden;border:0.5px solid var(--dsw-alias-settings-card-stroke);border-radius:var(--dsw-radius-xl);background:var(--dsw-alias-settings-card-fill)}
.card.开{border-color:var(--dsw-alias-border-l3)}
.card.失败{border-color:color-mix(in srgb,var(--dsw-alias-state-error-primary) 45%,transparent)}
button.cardContent{box-sizing:border-box;display:flex;flex:1 1 auto;flex-direction:column;align-items:stretch;gap:2px;width:100%;min-height:52px;border:0;padding:12px 14px;background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer}
button.cardContent:hover,.card.开>button.cardContent{background:var(--dsw-alias-interactive-bg-hover)}
.cardMainRow{display:flex;align-items:center;justify-content:space-between;gap:12px;min-width:0;width:100%}
.cardTitle,.cardIdentity{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cardTitle{flex:1;min-width:0;font-size:14px;line-height:20px;font-weight:500}
.cardDescription{display:-webkit-box;overflow:hidden;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;-webkit-box-orient:vertical;-webkit-line-clamp:2}
.card.开 .cardDescription{display:block}
.cardMeta{display:flex;margin-top:auto;padding-top:6px}
.cardIdentity,.entryValue{font-family:var(--ds-font-family-code);font-size:12px;line-height:18px}
.cardIdentity{display:block;box-sizing:border-box;max-width:100%;border-radius:var(--dsw-radius-xs);padding:1px 6px;background:var(--dsw-alias-bg-module-platform);color:var(--dsw-alias-label-secondary)}
.cardTrailing{display:inline-flex;flex:none;align-items:center;gap:8px;color:var(--dsw-alias-label-tertiary)}
.phaseDot{display:inline-flex;flex:none}
.tag{display:inline-flex;align-items:center;border-radius:999px;padding:1px 8px;font-size:11px;line-height:17px;font-weight:500;white-space:nowrap}
.tag[data-tone=neutral]{background:var(--dsw-alias-bg-module-platform);color:var(--dsw-alias-label-secondary)}
.tag[data-tone=info]{background:color-mix(in srgb,var(--dsw-alias-state-business-primary) 10%,transparent);color:var(--dsw-alias-state-business-primary)}
.tag[data-tone=warning]{background:color-mix(in srgb,var(--dsw-alias-state-warn-primary) 12%,transparent);color:var(--dsw-alias-state-warn-primary)}
.tag[data-tone=danger]{background:color-mix(in srgb,var(--dsw-alias-state-error-primary) 10%,transparent);color:var(--dsw-alias-state-error-primary)}
.group{display:flex;flex-direction:column;gap:10px}
.groupTitleRow{display:flex;align-items:center;gap:8px;min-height:36px}
.group+.group{border-top:0.5px solid var(--dsw-alias-border-l2);padding-top:14px}
.headerEnd{margin-left:auto}
button.groupToggle{display:flex;flex:none;align-items:center;gap:8px;border:0;padding:0;background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer}
button.groupToggle .chevron{transform:rotate(-90deg)}
button.groupToggle.展开 .chevron{transform:none}
.groupTitle{font-size:14px;line-height:22px;font-weight:400;color:var(--dsw-alias-label-primary)}
.groupSub{display:flex;flex-wrap:wrap;row-gap:4px;margin:-6px 0 0 20px;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;font-variant-numeric:tabular-nums}
.groupSub>*+*::before{content:'·';padding:0 6px;color:var(--dsw-alias-label-tertiary)}
.failedCount{color:var(--dsw-alias-state-error-primary)}
button.switcher{display:inline-flex;flex:none;align-items:center;gap:12px;height:36px;white-space:nowrap;border:none;border-radius:var(--dsw-radius-md);padding:0 14px;background:var(--dsw-alias-bg-module-platform);color:var(--dsw-alias-label-primary);font:inherit;font-size:14px;line-height:22px;cursor:pointer}
.switcherLabel{max-width:240px;overflow:hidden;text-overflow:ellipsis}
.groupBody{display:flex;flex-direction:column;gap:10px}
.brokenNote{margin:0;border-radius:var(--dsw-radius-lg);padding:8px 10px;background:color-mix(in srgb,var(--dsw-alias-state-error-primary) 8%,transparent);color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px;overflow-wrap:anywhere;white-space:pre-line}
.hint{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 8px;margin:0;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
button.jumpLink{border:0;padding:0;background:transparent;color:var(--dsw-alias-state-business-primary);font:inherit;font-size:12px;cursor:pointer}
.skeletonCard{display:flex;flex-direction:column;gap:8px;border:0.5px solid var(--dsw-alias-settings-card-stroke);border-radius:var(--dsw-radius-xl);padding:15px 14px;background:var(--dsw-alias-settings-card-fill)}
.skeletonBar{display:block;width:40%;height:14px;border-radius:var(--dsw-radius-xs);background:var(--dsw-alias-bg-skeleton)}
.skeletonBar+.skeletonBar{width:80%;height:12px}
.enabledIn{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px}
.chevron{flex:none;color:var(--dsw-alias-label-tertiary)}
.card.开 .chevron{transform:rotate(180deg)}
.cardDetails{border-top:0.5px solid var(--dsw-alias-border-l2);padding:10px 14px 12px;background:var(--dsw-alias-bg-module-platform)}
.entryValue{display:block;overflow-wrap:anywhere;color:var(--dsw-alias-label-primary)}
.details{display:grid;grid-template-columns:76px minmax(0,1fr);gap:6px 10px;margin:8px 0 0}
.factLabel{color:var(--dsw-alias-label-tertiary);font-size:11px;line-height:17px}
.factValue{min-width:0;margin:0;overflow-wrap:anywhere;color:var(--dsw-alias-label-secondary);font-size:12px;line-height:17px}
.visuallyHidden{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (prefers-reduced-motion:no-preference){.chevron{transition:transform 140ms var(--ds-ease-in-out)}.skeletonBar{animation:plugin-inventory-skeleton 2s cubic-bezier(0.36,0,0.64,1) infinite}}
@keyframes plugin-inventory-skeleton{0%{opacity:1}40%{opacity:0.6}80%,100%{opacity:1}}
@container plugin-inventory (max-width:520px){.cards{grid-template-columns:minmax(0,1fr)}}
'''

def _去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def _前缀一片(片,根):
    '同一元素与后代都能命中'
    片=片.strip()
    if 片=='':
        return ''
    return '.'+根+' '+片+', .'+根+片

def _前缀选择器(选择器,根):
    '逗号分隔的每一段都挂上根'
    条=[]
    for 片 in 选择器.split(','):
        已=_前缀一片(片,根)
        if 已!='':
            条.append(已)
    return ', '.join(条)

def _挂规则(文,根):
    '普通规则挂根；媒体查询递归；关键帧保持原样'
    出=[]
    下标=0
    长度=len(文)
    while 下标<长度:
        while 下标<长度 and 文[下标].isspace():
            下标+=1
        if 下标>=长度:
            break
        起=下标
        while 下标<长度 and 文[下标]!='{':
            下标+=1
        if 下标>=长度:
            break
        选择器=文[起:下标].strip()
        下标+=1
        深度=1
        体起=下标
        while 下标<长度 and 深度>0:
            if 文[下标]=='{':
                深度+=1
            elif 文[下标]=='}':
                深度-=1
            下标+=1
        体=文[体起:下标-1]
        if 选择器.startswith('@keyframes') or 选择器.startswith('@font-face'):
            出.append(选择器+'{'+体+'}')
        elif 选择器.startswith('@media') or 选择器.startswith('@container') or 选择器.startswith('@supports'):
            出.append(选择器+'{'+_挂规则(体,根)+'}')
        elif 选择器!='':
            出.append(_前缀选择器(选择器,根)+'{'+体+'}')
    return '\n'.join(出)

界面.add_css(_挂规则(_去注释(样式表),'插件清单根'),shared=True)
界面.add_css(点样式,shared=True)

def 模块短名(模块名):#压缩模块说明符
    '去掉作用域与常见前缀，不猜测 Loader id'
    去作用域=模块名[模块名.index('/')+1:] if 模块名.startswith('@') else 模块名#去作用域
    名=去作用域#工作副本
    if 名.startswith('cordis:'):#cordis 协议
        名=名[7:]#去掉
    if 名.startswith('cordis-plugin-'):#插件前缀
        名=名[14:]#去掉
    if 名.startswith('dsh-host-'):#宿主前缀
        名=名[9:]#去掉
    elif 名.startswith('dsh-client-'):#客户端前缀
        名=名[11:]#去掉
    elif 名.startswith('dsh-'):#通用 dsh
        名=名[4:]#去掉
    return 名#短名

def 入口副标题(入口标识):#去掉 include: 标记
    '组合标记不出现在卡片副标题'
    if isinstance(入口标识,str) and 入口标识.startswith('include:'):#有标记
        return 入口标识[8:]#去掉
    return 入口标识#原样

def 标识补充标题(入口标识,标题):#副标题是否多出信息
    '有入口 id，且去掉 include: 后仍不同于标题'
    if not isinstance(入口标识,str):#无 id
        return False#不显示
    return 入口副标题(入口标识)!=标题#不同才显示

def 插件文案(行,解析文案):#标题与说明
    '翻译过的标题保持译文；字面包名再缩短'
    元=行['meta'] if 'meta' in 行 and isinstance(行['meta'],dict) else {}#元数据
    标题=元['title'] if 'title' in 元 else None#标题原文
    模块=行['moduleName'] if 'moduleName' in 行 and isinstance(行['moduleName'],str) else ''#模块名
    if isinstance(标题,dict):#本地化映射
        显示=解析文案(标题) if callable(解析文案) else ''#解析
    elif isinstance(标题,str):#字面标题
        显示=模块短名(标题)#缩短
    else:#回退模块名
        显示=模块短名(模块)#缩短
    描述=None#说明
    if 'description' in 元 and 元['description'] is not None:#有说明
        原文=解析文案(元['description']) if callable(解析文案) else ''#解析
        if isinstance(原文,str) and 原文!='':#非空
            描述=原文#采用
    return {'title':显示,'description':描述}#文案

def 条目匹配(条目,规范化查询,解析文案=None):#查询是否命中
    '空查询全中；模块名、入口、标题、说明任一包含即命中'
    if len(规范化查询)==0:#空查询
        return True#全中
    文案=插件文案(条目,解析文案)#标题说明
    候选=(#候选
        条目['moduleName'] if 'moduleName' in 条目 else None,#模块
        条目['entryId'] if 'entryId' in 条目 else None,#入口
        文案['title'],#标题
        文案['description'],#说明
    )#候选结束
    for 值 in 候选:#逐个
        if isinstance(值,str) and 规范化查询 in 值.lower():#包含
            return True#命中
    return False#未命中

def 阶段标签(阶段,翻译):#阶段无障碍文案
    'null 阶段为未挂载'
    if 阶段 is None or 阶段 not in 阶段文案键:#未观察
        return 翻译('unobserved')#未挂载
    return 翻译(阶段文案键[阶段])#阶段文案

def 有阶段点(阶段):#该阶段是否自带点
    'pending、loading、unloading 才有点'
    return 阶段 in 阶段点态#有点

def 填文案(翻译,键,参数=None):#带占位的文案
    '无参数直接取词'
    if 参数 is None:#无占位
        return 翻译(键)#词
    return 翻译(键,参数)#替换

def 回退预设(预设表):#未手选时的预设
    '默认预设，否则第一项'
    for 预设 in 预设表:#逐个
        if 'isDefault' in 预设 and 预设['isDefault'] is True:#默认
            return 预设#用它
    if len(预设表)==0:#空
        return None#无
    return 预设表[0]#第一项

def 预设选项文案(预设,翻译,预设名):#切换器一项的文案
    '失败、默认各有后缀'
    名=预设名(预设)#显示名
    if 'broken' in 预设 and 预设['broken'] is not None:#加载失败
        return 填文案(翻译,'presetOptionBroken',{'name':名})#失败后缀
    if 'isDefault' in 预设 and 预设['isDefault'] is True:#默认
        return 填文案(翻译,'presetOptionDefault',{'name':名})#默认后缀
    return 名#原名

class 阶段点:#阶段状态点
    '父组件调用渲染；构造不画'
    def __init__(自身,属性):#构造
        '记下阶段与文案'
        自身.属性=属性#props

    def 渲染(自身):#画出点
        '进行中走共享状态点；等待用空闲色'
        文=自身.属性['label']#无障碍名
        安全=str(文).replace('"','')#属性值
        盒=界面.element('span').classes('phaseDot')#包装
        盒.props('role=img aria-label="'+安全+'" title="'+安全+'"')#名字
        态=自身.属性['state']#点态
        with 盒:#内容
            if 态=='ongoing':#进行中
                状态点({'state':'ongoing','size':10}).渲染()#转圈
            else:#等待
                界面.html('<span aria-hidden="true" class="状态点 点" data-state="idle" style="width:10px;height:10px"></span>',sanitize=False)#空闲点

class 状态标签:#启用状态胶囊
    '父组件调用渲染；已启用不画标签'
    def __init__(自身,属性):#构造
        '记下种类与文案'
        自身.属性=属性#props

    def 渲染(自身):#画出标签
        '已启用不画'
        种类=自身.属性['kind']#种类
        if 种类=='enabled' or 种类 not in 标签调:#默认启用
            return#不画
        界面.label(自身.属性['label']).classes('tag').props('data-tone='+标签调[种类])#胶囊

class 卡片事实:#展开后的事实表
    '父组件调用渲染'
    def __init__(自身,属性):#构造
        '记下模块、入口与事实行'
        自身.属性=属性#props

    def 渲染(自身):#画出事实
        '先入口 id，再标签与值'
        入口=自身.属性['entryId']#入口
        if isinstance(入口,str):#有入口
            界面.label(入口).classes('entryValue')#入口行
        with 界面.element('div').classes('details'):#表
            界面.label(自身.属性['moduleLabel']).classes('factLabel')#模块标签
            界面.label(自身.属性['moduleName']).classes('factValue')#模块值
            for 事实 in 自身.属性['facts']:#其余事实
                界面.label(事实['label']).classes('factLabel')#标签
                值=事实['value']#值
                if isinstance(值,dict) and 'kind' in 值 and 值['kind']=='enabledIn':#启用于
                    with 界面.element('div').classes('factValue enabledIn'):#值
                        界面.label(值['names'])#预设名
                        def 点跳(回调=值['onJump']):#跳到预设
                            '切到提供该模块的预设'
                            回调()#调用
                        钮=界面.element('button').classes('jumpLink').props('type=button')#链
                        钮.on('click',点跳)#点击
                        with 钮:#文案
                            界面.label(值['jumpLabel'])#去查看
                    continue#下一条
                if isinstance(值,dict) and 'kind' in 值 and 值['kind']=='code':#代码
                    界面.label(值['text']).classes('factValue')#条件
                    continue#下一条
                界面.label('' if 值 is None else str(值)).classes('factValue')#文本

class 插件卡片:#可展开的一张插件卡
    '父组件调用渲染'
    def __init__(自身,属性):#构造
        '记下卡片数据'
        自身.属性=属性#props

    def 渲染(自身):#画出卡片
        '标题行、说明、入口副标题，展开后是事实'
        属性=自身.属性#props
        类名='card'+(' 开' if 属性['open'] is True else '')+(' 失败' if 属性['failed'] is True else '')#类
        卡=界面.element('li').classes(类名)#卡片
        入口=属性['entryId']#入口
        标记=[]#数据属性
        if isinstance(入口,str) and 入口!='':#有入口
            标记.append('data-plugin-entry="'+入口.replace('"','')+'"')#入口
        模块=属性['moduleName'] if isinstance(属性['moduleName'],str) else ''#模块
        if 模块!='':#有模块
            标记.append('data-plugin-module="'+模块.replace('"','')+'"')#模块
        if len(标记)>0:#有标记
            卡.props(' '.join(标记))#写上
        with 卡:#内容
            def 点卡():#展开或收起
                '交给页签切换'
                属性['onToggle'](属性['rowKey'])#切换
            钮=界面.element('button').classes('cardContent').props('type=button')#按钮
            钮.props('aria-expanded='+('true' if 属性['open'] is True else 'false'))#展开态
            钮.props('aria-label="'+str(属性['ariaLabel']).replace('"','')+'"')#无障碍名
            钮.on('click',点卡)#点击
            with 钮:#按钮内容
                with 界面.element('span').classes('cardMainRow'):#标题行
                    界面.label(属性['title']).classes('cardTitle')#标题
                    with 界面.element('span').classes('cardTrailing'):#尾部
                        for 尾 in 属性['trailing']:#点或标签
                            if 尾['kind']=='phase':#阶段点
                                阶段点({'state':尾['state'],'label':尾['label']}).渲染()#画点
                            elif 尾['kind']=='tag':#状态标签
                                状态标签({'kind':尾['tagKind'],'label':尾['label']}).渲染()#画标签
                        图标下chevron14({'className':'chevron','size':12})#箭头
                描述=属性['description']#说明
                if isinstance(描述,str) and 描述!='':#有说明
                    界面.label(描述).classes('cardDescription')#说明
                if 标识补充标题(入口,属性['title']) is True:#副标题有信息
                    with 界面.element('span').classes('cardMeta'):#元信息
                        界面.label(入口副标题(入口)).classes('cardIdentity')#短入口
            元错=属性['metadataError']#元信息错误
            if isinstance(元错,str) and 元错!='':#有错误
                界面.label(元错).classes('brokenNote')#错误条
            if 属性['open'] is True:#已展开
                with 界面.element('div').classes('cardDetails'):#详情
                    卡片事实(属性['facts']).渲染()#事实

class 切换锚:#预设菜单的锚按钮
    '菜单在绘制锚时调用渲染；构造不画'
    def __init__(自身,属性):#构造
        '记下标签与点击'
        自身.属性=属性#props

    def 渲染(自身):#画出切换按钮
        '标签与箭头'
        钮=界面.element('button').classes('switcher').props('type=button aria-haspopup=menu')#按钮
        钮.props('aria-expanded='+('true' if 自身.属性['open'] is True else 'false'))#开合
        钮.props('aria-label="'+str(自身.属性['aria']).replace('"','')+'"')#无障碍名
        钮.on('click',自身.属性['onClick'])#开关
        with 钮:#内容
            界面.label(自身.属性['label']).classes('switcherLabel')#当前预设
            图标下chevron14({'className':'chevron'})#箭头

class 插件清单页签:#设置页签组件
    '只读当前 Loader 清单；预设分组在前，全局平面在后'
    def __init__(自身,属性):#按合成 props 构造
        '槽位只调用构造。键齐后拉清单，由拉取在末尾画'
        自身.属性=属性#合成 props
        自身.查询=''#搜索框
        自身.展开标识=None#展开的行键
        自身.所选预设=None#手选预设 id
        自身.切换器开=False#预设菜单
        自身.预设展开=None#None 表示默认展开
        自身.全局展开=None#None 表示默认折叠
        自身.状态={'status':'loading'}#视图状态
        自身.存活=True#实例存活
        自身.根=None#页面根
        自身.画面失败=None
        if 't' in 自身.属性:
            自身.拉取()#键齐后拉清单，由拉取在末尾画

    def 更新(自身,属性):#props 变更
        '刷新合成 props'
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 解析文案(自身,文本):#包内文案
        '缺注入时字符串原样，映射取中文或英文'
        解析=自身.属性['resolveText'] if 'resolveText' in 自身.属性 else None#注入
        if callable(解析):
            return 解析(文本)#解析
        if isinstance(文本,str):#字符串
            return 文本#原样
        if isinstance(文本,dict) and 'zh' in 文本 and 文本['zh'] is not None:#中文
            return 文本['zh']#中文
        if isinstance(文本,dict) and 'en' in 文本 and 文本['en'] is not None:#英文
            return 文本['en']#英文
        return ''#空

    def 本页同步(自身):#读本页同步快照
        'useClientSync 缺席时当作未同步、无失败'
        用=自身.属性['useClientSync'] if 'useClientSync' in 自身.属性 else None#钩子
        if not callable(用):#未绑定
            return {'syncing':False,'failures':[]}#空
        快照=用(lambda 值:值)#整份
        if not isinstance(快照,dict):#不是快照
            return {'syncing':False,'failures':[]}#空
        失败=快照['failures'] if 'failures' in 快照 and isinstance(快照['failures'],list) else []#失败
        同步中='syncing' in 快照 and 快照['syncing'] is True#进行中
        return {'syncing':同步中,'failures':失败}#投影

    def 拉取(自身):#拉取清单
        '按 list 注入面读快照'
        列表=自身.属性['list'] if 'list' in 自身.属性 else None#远程 list
        if not callable(列表):#没有
            if 自身.存活 is True:#仍在
                自身.状态={'status':'error'}#错误
                自身.渲染()#重画
            return
        try:#拉取
            快照=列表()#结算
        except Exception as 错误:
            if 自身.存活 is not True:#已死
                return#丢弃
            自身.状态={'status':'error','detail':页面失败文案(错误)}
            自身.渲染()#重画
            return
        if 自身.存活 is not True:#已死
            return#丢弃
        if not isinstance(快照,dict):#不是清单
            自身.状态={'status':'error'}#错误
            自身.渲染()#重画
            return
        自身.状态={'status':'ready','snapshot':快照}#就绪
        自身.渲染()#重画

    def 重试(自身):#失败后重试
        '先画读取中再拉'
        自身.状态={'status':'loading'}#读中
        自身.渲染()#骨架
        自身.拉取()#再拉

    def 设查询(自身,文本):#改搜索
        '更新查询'
        自身.查询='' if 文本 is None else str(文本)#查询

    def 切换展开(自身,行键):#展开或收起
        '同一键再点则收起'
        自身.展开标识=None if 自身.展开标识==行键 else 行键#切换

    def 跳预设(自身,标识):#切到某个预设
        '关闭菜单并选中'
        自身.所选预设=标识#选中
        自身.切换器开=False#关菜单

    def 预设行数据(自身,预设,行,下标,翻译,预设名):#一张预设卡的数据
        '失败、启用、停用、条件启用'
        键='preset:'+str(预设['id'] if 'id' in 预设 else '')+':'+str(下标)#行键
        文案=插件文案(行,自身.解析文案)#标题
        阶段=行['fiberPhase'] if 'fiberPhase' in 行 else None#阶段
        失败=阶段=='failed'#失败
        启用=行['enabled'] if 'enabled' in 行 else None#启用
        if 失败 is True:#失败
            状态文=翻译('failedTag')#失败
            种类='failed'#种类
        elif 启用 is True:#启用
            状态文=翻译('enabledTag')#启用
            种类='enabled'#种类
        elif 启用 is False:#停用
            状态文=翻译('disabledTag')#停用
            种类='disabled'#种类
        else:#条件
            状态文=翻译('conditionalTag')#条件
            种类='conditional'#种类
        尾=[]#尾部
        if 启用 is True and 有阶段点(阶段) is True:#有点
            尾.append({'kind':'phase','state':阶段点态[阶段],'label':阶段标签(阶段,翻译)})#点
        尾.append({'kind':'tag','tagKind':种类,'label':状态文})#标签
        事实=[]#详情
        事实.append({'label':翻译('fromPreset'),'value':预设名(预设)})#来自
        事实.append({'label':翻译('configuration'),'value':状态文})#配置
        if 阶段 is not None:#有运行态
            事实.append({'label':翻译('runtime'),'value':阶段标签(阶段,翻译)})#运行
        if 'condition' in 行 and 行['condition'] is not None:#有条件
            事实.append({'label':翻译('condition'),'value':{'kind':'code','text':行['condition']}})#条件
        元=行['meta'] if 'meta' in 行 and isinstance(行['meta'],dict) else {}#元数据
        元错=None#元信息错误
        if 'error' in 元 and 元['error'] is not None:#有错误
            元错=填文案(翻译,'metadataError',{'error':页面失败文案(元['error'])})#文案
        return {#卡片
            'rowKey':键,#键
            'moduleName':行['moduleName'] if 'moduleName' in 行 else '',#模块
            'title':文案['title'],#标题
            'description':文案['description'],#说明
            'metadataError':元错,#元信息错误
            'entryId':行['entryId'] if 'entryId' in 行 else None,#入口
            'failed':失败,#失败
            'open':自身.展开标识==键,#展开
            'ariaLabel':(文案['title']+', '+str(行['entryId'])+', '+状态文) if 标识补充标题(行['entryId'] if 'entryId' in 行 else None,文案['title']) else (文案['title']+', '+状态文),#无障碍
            'trailing':尾,#尾部
            'onToggle':自身.点行,#切换
            'facts':{#事实块
                'moduleName':行['moduleName'] if 'moduleName' in 行 else '',#模块
                'moduleLabel':翻译('moduleLabel'),#标签
                'entryId':行['entryId'] if 'entryId' in 行 else None,#入口
                'facts':事实,#行
            },#事实结束
        }#卡片结束

    def 全局行数据(自身,条目,提供方,翻译,预设名):#一张全局卡的数据
        '失败优先；未启用且有预设提供时标成预设启用'
        入口=条目['entryId'] if 'entryId' in 条目 else None#入口
        键='global:'+str(入口)#行键
        文案=插件文案(条目,自身.解析文案)#标题
        阶段=条目['fiberPhase'] if 'fiberPhase' in 条目 else None#阶段
        失败=阶段=='failed'#失败
        启用='enabled' in 条目 and 条目['enabled'] is True#启用
        if 失败 is True:#失败
            状态文=翻译('failedTag')#失败
            种类='failed'#种类
        elif 提供方 is not None:#预设提供
            状态文=翻译('presetEnabledTag')#预设
            种类='preset'#种类
        elif 启用 is True:#启用
            状态文=翻译('enabledTag')#启用
            种类='enabled'#种类
        else:#停用
            状态文=翻译('disabledTag')#停用
            种类='disabled'#种类
        尾=[]#尾部
        if 启用 is True and 有阶段点(阶段) is True:#有点
            尾.append({'kind':'phase','state':阶段点态[阶段],'label':阶段标签(阶段,翻译)})#点
        尾.append({'kind':'tag','tagKind':种类,'label':状态文})#标签
        if 提供方 is not None:#预设提供
            def 点跳(标识=提供方[0]['id'] if 'id' in 提供方[0] else None):#去第一个预设
                '切到提供方'
                自身.跳预设(标识)#跳
                自身.渲染()#重画
            事实=[#事实
                {'label':翻译('configuration'),'value':翻译('presetProvidedDetail')},#配置说明
                {'label':翻译('enabledIn'),'value':{#启用于
                    'kind':'enabledIn',#种类
                    'names':' · '.join(预设名(项) for 项 in 提供方),#名字
                    'jumpLabel':翻译('viewInPreset'),#链接
                    'onJump':点跳,#跳
                }},#启用于结束
            ]#事实结束
        else:#普通全局行
            事实=[{'label':翻译('configuration'),'value':翻译('enabledTag' if 启用 is True else 'disabledTag')}]#配置
            if 启用 is True:#已启用才有运行态
                事实.append({'label':翻译('runtime'),'value':阶段标签(阶段,翻译)})#运行
        元=条目['meta'] if 'meta' in 条目 and isinstance(条目['meta'],dict) else {}#元数据
        元错=None#元信息错误
        if 'error' in 元 and 元['error'] is not None:#有错误
            元错=填文案(翻译,'metadataError',{'error':页面失败文案(元['error'])})#文案
        return {#卡片
            'rowKey':键,#键
            'moduleName':条目['moduleName'] if 'moduleName' in 条目 else '',#模块
            'title':文案['title'],#标题
            'description':文案['description'],#说明
            'metadataError':元错,#元信息错误
            'entryId':入口,#入口
            'failed':失败,#失败
            'open':自身.展开标识==键,#展开
            'ariaLabel':(文案['title']+', '+str(入口)+', '+状态文) if 标识补充标题(入口,文案['title']) else (文案['title']+', '+状态文),#无障碍
            'trailing':尾,#尾部
            'onToggle':自身.点行,#切换
            'facts':{#事实块
                'moduleName':条目['moduleName'] if 'moduleName' in 条目 else '',#模块
                'moduleLabel':翻译('moduleLabel'),#标签
                'entryId':入口,#入口
                'facts':事实,#行
            },#事实结束
        }#卡片结束

    def 点行(自身,行键):#展开回调
        '切换后重画'
        自身.切换展开(行键)#切换
        自身.渲染()#重画

    def 启用表(自身,预设表):#模块 → 真正启用它的预设
        '只记 enabled 为真的行'
        找到={}#表
        for 预设 in 预设表:#每个预设
            行表=预设['rows'] if 'rows' in 预设 and isinstance(预设['rows'],list) else []#行
            for 行 in 行表:#每行
                if ('enabled' in 行 and 行['enabled'] is True) is not True:#未启用
                    continue#跳过
                模块=行['moduleName'] if 'moduleName' in 行 else None#模块
                if not isinstance(模块,str):#无模块名
                    continue#跳过
                if 模块 not in 找到:#首个
                    找到[模块]=[预设]
                elif all(项 is not 预设 for 项 in 找到[模块]):#尚未记过这一份
                    找到[模块].append(预设)#追加
        return 找到#表

    def 渲染(自身):#画出页签
        '同步条、骨架或错误、搜索，以及预设与全局两组卡片'
        翻译=自身.属性['t']#文案
        旧=getattr(自身,'根',None)#已有根
        自身.画面失败=None
        if 旧 is not None:#重画
            try:#清掉旧节点
                旧.clear()#清空
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        if getattr(自身,'根',None) is None:#尚无根
            自身.根=界面.column().classes('插件清单根 section')#页
        同步=自身.本页同步()#本页同步
        区号=str(id(自身))#分组 id
        with 自身.根:#页面
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败).classes('failure')
            if 同步['syncing'] is True:#同步中
                with 界面.row().classes('status statusWithDot'):#状态
                    状态点({'state':'ongoing','size':10}).渲染()#点
                    界面.label(翻译('clientSyncing'))#文案
            if len(同步['failures'])>0:#有失败
                with 界面.column().classes('failure'):#失败块
                    with 界面.row().classes('statusWithDot'):#标题
                        状态点({'state':'error','size':10}).渲染()#点
                        界面.label(翻译('clientSyncFailed'))#文案
                    with 界面.element('ul'):#列表
                        for 失败 in 同步['failures']:#每条
                            标识=失败['id'] if isinstance(失败,dict) and 'id' in 失败 else ''#id
                            消息=失败['message'] if isinstance(失败,dict) and 'message' in 失败 else ''
                            if 消息!='':
                                消息=页面失败文案(消息)
                            with 界面.element('li'):#行
                                界面.label(str(标识)+': '+str(消息))#文本
                    def 点本页():#重试本页同步
                        '不改宿主启用态'
                        重试本页=自身.属性['retryClient'] if 'retryClient' in 自身.属性 else None#回调
                        if callable(重试本页):
                            重试本页()#调用
                    本页钮=界面.element('button').classes('failureButton').props('type=button')#按钮
                    if 同步['syncing'] is True:#进行中
                        本页钮.props('disabled')#禁用
                    本页钮.on('click',点本页)#点击
                    with 本页钮:#文案
                        界面.label(翻译('clientSyncRetry'))#重试
            if 自身.状态['status']=='loading':#读取中
                with 界面.element('div').classes('cards'):#骨架格
                    界面.label(翻译('loading')).classes('visuallyHidden')#无障碍
                    for _格 in 骨架格:#四张
                        with 界面.element('div').classes('skeletonCard'):#卡
                            界面.element('span').classes('skeletonBar')#条
                            界面.element('span').classes('skeletonBar')#条
            if 自身.状态['status']=='error':#失败
                with 界面.column().classes('failure'):#失败块
                    with 界面.row().classes('statusWithDot'):#标题
                        状态点({'state':'error','size':10}).渲染()#点
                        界面.label(翻译('error'))#文案
                    细节=自身.状态['detail'] if 'detail' in 自身.状态 else None
                    if isinstance(细节,str) and 细节!='':
                        界面.label(细节)
                    def 点重试():#再拉清单
                        '回到读取中'
                        自身.重试()#再拉
                    重试钮=界面.element('button').classes('failureButton').props('type=button')#按钮
                    重试钮.on('click',点重试)#点击
                    with 重试钮:#文案
                        界面.label(翻译('retry'))#重试
            if 自身.状态['status']!='ready':#未就绪
                return#同步条和骨架或错误已经画完
            快照=自身.状态['snapshot']#清单
            预设表=快照['agentPresets'] if 'agentPresets' in 快照 and isinstance(快照['agentPresets'],list) else []#预设
            条目表=快照['entries'] if 'entries' in 快照 and isinstance(快照['entries'],list) else []#全局
            规范化=自身.查询.strip().lower()#查询
            搜索中=len(规范化)>0#正在搜
            选中=None#当前预设
            for 预设 in 预设表:#按手选找
                if 'id' in 预设 and 预设['id']==自身.所选预设:#命中
                    选中=预设#用它
                    break
            if 选中 is None:#未手选或已消失
                选中=回退预设(预设表)#默认
            预设名=自身.属性['presetName'] if 'presetName' in 自身.属性 and callable(自身.属性['presetName']) else (lambda 预设: 预设['name'] if 'name' in 预设 and isinstance(预设['name'],str) and 预设['name']!='' else (预设['id'] if 'id' in 预设 else ''))#显示名
            启用于=自身.启用表(预设表)#预设提供
            失败条目=[]#失败
            普通条目=[]#其余
            for 条目 in 条目表:#分组
                if ('fiberPhase' in 条目 and 条目['fiberPhase']=='failed') is True:#失败
                    失败条目.append(条目)#失败组
                else:#其余
                    普通条目.append(条目)#普通组
            过滤失败=[条目 for 条目 in 失败条目 if 条目匹配(条目,规范化,自身.解析文案)]#失败过滤
            过滤普通=[条目 for 条目 in 普通条目 if 条目匹配(条目,规范化,自身.解析文案)]#普通过滤
            全局数=len(过滤失败)+len(过滤普通)#全局计数
            选中行=[]#当前预设的行
            if 选中 is not None:#有预设
                行表=选中['rows'] if 'rows' in 选中 and isinstance(选中['rows'],list) else []#行
                选中行=[行 for 行 in 行表 if 条目匹配(行,规范化,自身.解析文案)]#过滤
            其它预设=[]#其它预设里的命中
            if 搜索中 is True:#搜索才提示
                for 预设 in 预设表:#逐个
                    if 预设 is 选中:#当前
                        continue#跳过
                    行表=预设['rows'] if 'rows' in 预设 and isinstance(预设['rows'],list) else []#行
                    if any(条目匹配(行,规范化,自身.解析文案) for 行 in 行表):#有命中
                        其它预设.append(预设)
            其它数=0#其它命中数
            for 预设 in 其它预设:#计数
                行表=预设['rows'] if 'rows' in 预设 and isinstance(预设['rows'],list) else []#行
                其它数+=len([行 for 行 in 行表 if 条目匹配(行,规范化,自身.解析文案)])#加
            预设开=搜索中 is True or (自身.预设展开 if 自身.预设展开 is not None else True)#预设组展开
            全局开=搜索中 is True or (自身.全局展开 if 自身.全局展开 is not None else False)#全局组展开
            全无=搜索中 is True and 全局数==0 and len(选中行)==0 and len(其它预设)==0#没有匹配
            with 界面.column().classes('catalog'):#目录
                with 界面.element('div').classes('search'):#搜索
                    with 界面.element('span').classes('searchIcon'):#图标
                        图标检索16()#搜索
                    def 改查询(事件):#输入
                        '过滤两组卡片'
                        文本='' if 事件.value is None else str(事件.value)#文本
                        if 文本==自身.查询:#未变
                            return
                        自身.设查询(文本)
                        自身.渲染()#重画
                    界面.input(placeholder=翻译('search'),value=自身.查询,on_change=改查询).classes('searchInput').props('aria-label="'+翻译('search').replace('"','')+'"')#框
                if len(条目表)==0 and len(预设表)==0:#空清单
                    界面.label(翻译('empty')).classes('status')#空
                if 全无 is True:#搜索无匹配
                    界面.label(翻译('emptySearch')).classes('status')#无匹配
                if 选中 is not None:#预设组
                    def 点预设组(当前=预设开):#折叠预设组
                        '搜索期间仍保持展开'
                        自身.预设展开=not 当前
                        自身.渲染()#重画
                    def 点切换():#开关菜单
                        '翻转开合'
                        自身.切换器开=自身.切换器开 is not True#翻转
                        自身.渲染()#重画
                    def 选定(标识):#选一个预设
                        '关掉菜单'
                        自身.跳预设(标识)#选中
                        自身.渲染()#重画
                    def 关闭菜单():#菜单要求关闭
                        '已经关着则不再重画'
                        if 自身.切换器开 is not True:#已关
                            return
                        自身.切换器开=False#关
                        自身.渲染()#重画
                    区=界面.element('section').classes('group')#组
                    区.props('data-plugin-scope=preset')#范围
                    if 'id' in 选中:#有 id
                        区.props('data-preset-id="'+str(选中['id']).replace('"','')+'"')#id
                    with 区:#内容
                        with 界面.row().classes('groupTitleRow'):#标题行
                            组钮=界面.element('button').classes('groupToggle'+(' 展开' if 预设开 is True else '')).props('type=button')#折叠
                            组钮.props('aria-expanded='+('true' if 预设开 is True else 'false'))#展开
                            组钮.props('aria-controls='+区号+'-preset')#控制
                            组钮.on('click',点预设组)#点击
                            with 组钮:#标题
                                图标下chevron14({'className':'chevron','size':12})#箭头
                                界面.label(翻译('presetTitle')).classes('groupTitle')#标题
                            with 界面.element('div').classes('headerEnd'):#右侧
                                菜单({#预设菜单
                                    'open':自身.切换器开 is True,
                                    'align':'end',#靠右
                                    'items':[{'id':预设['id'] if 'id' in 预设 else None,'label':预设选项文案(预设,翻译,预设名)} for 预设 in 预设表],#项
                                    'selectedId':选中['id'] if 'id' in 选中 else None,#当前
                                    'onSelect':选定,#选定
                                    'onClose':关闭菜单,#关闭
                                    'anchor':切换锚({'label':预设选项文案(选中,翻译,预设名),'aria':翻译('switcherLabel'),'open':自身.切换器开 is True,'onClick':点切换}),#锚
                                }).渲染()#菜单
                        with 界面.row().classes('groupSub'):#副标题
                            界面.label(翻译('presetSubtitle'))#说明
                            界面.label(str(len(选中行))+' '+翻译('countUnit'))#计数
                        if 预设开 is True:#展开
                            with 界面.column().classes('groupBody'):#体
                                if 'broken' in 选中 and isinstance(选中['broken'],str) and 选中['broken']!='':#坏预设
                                    界面.label(选中['broken']).classes('brokenNote')#原因
                                if len(选中行)>0:#有卡
                                    with 界面.element('ul').classes('cards'):#网格
                                        for 下标,行 in enumerate(选中行):#每行
                                            插件卡片(自身.预设行数据(选中,行,下标,翻译,预设名)).渲染()#卡
                                if 其它数>0:#其它预设还有
                                    with 界面.element('p').classes('hint'):#提示
                                        界面.label(填文案(翻译,'matchesInOtherPresets',{'count':str(其它数)}))#文案
                                        for 预设 in 其它预设:#每个
                                            def 点其它(标识=预设['id'] if 'id' in 预设 else None):#跳过去
                                                '切预设'
                                                自身.跳预设(标识)#选
                                                自身.渲染()#重画
                                            链=界面.element('button').classes('jumpLink').props('type=button')#链
                                            链.on('click',点其它)#点击
                                            with 链:#名字
                                                界面.label(预设名(预设))#名
                if len(条目表)>0:#全局组
                    def 点全局组(当前=全局开):#折叠全局组
                        '搜索期间仍保持展开'
                        自身.全局展开=not 当前
                        自身.渲染()#重画
                    全区=界面.element('section').classes('group')#组
                    全区.props('data-plugin-scope=global')#范围
                    with 全区:#内容
                        with 界面.row().classes('groupTitleRow'):#标题行
                            全钮=界面.element('button').classes('groupToggle'+(' 展开' if 全局开 is True else '')).props('type=button')#折叠
                            全钮.props('aria-expanded='+('true' if 全局开 is True else 'false'))#展开
                            全钮.props('aria-controls='+区号+'-global')#控制
                            全钮.on('click',点全局组)#点击
                            with 全钮:#标题
                                图标下chevron14({'className':'chevron','size':12})#箭头
                                界面.label(翻译('globalTitle')).classes('groupTitle')#标题
                        with 界面.row().classes('groupSub'):#副标题
                            界面.label(翻译('globalSubtitle'))#说明
                            界面.label(str(全局数)+' '+翻译('countUnit'))#计数
                            if len(过滤失败)>0:#有失败
                                界面.label(str(len(过滤失败))+' '+翻译('failedCountLabel')).classes('failedCount')#失败数
                        if 全局开 is True and 全局数>0:#展开且有卡
                            with 界面.element('ul').classes('cards'):#网格
                                for 条目 in 过滤失败:#失败在前
                                    插件卡片(自身.全局行数据(条目,None,翻译,预设名)).渲染()#卡
                                for 条目 in 过滤普通:#其余
                                    模块=条目['moduleName'] if 'moduleName' in 条目 else None#模块
                                    提供=None#提供方
                                    if ('enabled' in 条目 and 条目['enabled'] is True) is not True and isinstance(模块,str) and 模块 in 启用于:#未启用且有预设
                                        提供=启用于[模块]#提供方
                                    插件卡片(自身.全局行数据(条目,提供,翻译,预设名)).渲染()#卡

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

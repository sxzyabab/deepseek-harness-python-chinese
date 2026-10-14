import importlib.resources as 包资源
from nicegui import ui as 界面
from .存储 import 推导密钥引用,错误文案,提供方可用,协议选项#存储辅助
from .提供方编辑器 import 提供方编辑器#编辑卡片
from .自定义提供方卡片 import 自定义提供方卡片#创建卡片

__all__=[
    '模型分区','需要装卡','移除提供方档案','编辑目标自','提供方目标标签','提供方文案',
]

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

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

def 挂到根(原文,根):
    '共享样式只作用在本组件根下'
    return _挂规则(_去注释(原文),根)

界面.add_css(挂到根(_读样式('模型分区.module.css'),'模型分区根'),shared=True)

def 需要装卡(行,任一可用):#首跑姿态下是否打开装卡
    '已有可用提供方则普通行；整段提供方且密钥未配才装卡'
    if 任一可用:#已有可用
        return False#普通行
    条目=行['entry'] if 'entry' in 行 and 行['entry'] is not None else {}#目录条目
    路径=条目['settingsPath'] if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else []#设置路径
    if len(路径)>0:#非整段
        return False#普通行
    凭证=行['credential'] if 'credential' in 行 else None#凭证态
    return 凭证 is None or 'configured' not in 凭证 or 凭证['configured'] is not True#未配置密钥

def 移除提供方档案(接口,控制器,目标):#移除用户添加的提供方及其页管凭证
    '先卸凭证再 unset 设置；失败文案或成功后 reload 返回 None'
    try:#写线
        凭证引用=目标['credentialRef'] if 'credentialRef' in 目标 else None#可选托管引用
        if 凭证引用 is not None:#有凭证
            凭证=接口.credentials.unset({'ref':凭证引用}).等待()#卸凭证
            结果=凭证['result']#结果
            if 结果['ok'] is not True:#失败
                错=结果['error'] if 'error' in 结果 else None#错误
                return 错误文案(错['message'] if 错 is not None and 'message' in 错 else None)
        路径=目标['settingsPath'] if 'settingsPath' in 目标 and 目标['settingsPath'] is not None else []#路径
        响应=接口.settings.mutate({#unset 档案
            'ns':目标['settingsNs'],
            'ops':[{'op':'unset','path':list(路径)}],
        }).等待()#变更
        结果=响应['result']#结果
        if 结果['ok'] is not True:#失败
            错=结果['error'] if 'error' in 结果 else None#错误
            return 错误文案(错['message'] if 错 is not None and 'message' in 错 else None)
    except Exception as 错误:#传输拒绝；RPC 异常契约未定
        return 错误文案(错误)#可重试
    控制器.load()#刷新页
    return None#成功

def 编辑目标自(行):#从接合行推导编辑器目标
    '托管凭证引用仅在约定引用且已配置可写时带上'
    条目=行['entry'] if 'entry' in 行 and 行['entry'] is not None else {}#条目
    路由=条目['provider'] if 'provider' in 条目 else ''#路由
    托管引用=推导密钥引用(路由)#约定引用
    凭证=行['credential'] if 'credential' in 行 else None#凭证
    环境=行['apiKeyEnv'] if 'apiKeyEnv' in 行 else None#环境
    已配=凭证 is not None and 'configured' in 凭证 and 凭证['configured'] is True#已配置
    可写=凭证 is not None and 'writable' in 凭证 and 凭证['writable']#可写
    凭证引用=None#默认不带
    if 环境==托管引用 and 已配 and 可写:#页管凭证
        凭证引用=托管引用#带上
    目标={#编辑目标
        'provider':条目['provider'] if 'provider' in 条目 else None,
        'displayName':条目['displayName'] if 'displayName' in 条目 else None,
        'settingsNs':条目['settingsNs'] if 'settingsNs' in 条目 else None,
        'settingsPath':list(条目['settingsPath']) if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else [],
    }#基础
    if 凭证引用 is not None:#有托管
        目标['credentialRef']=凭证引用#带上
    if 'declared' in 条目 and 条目['declared'] is True:#适配器声明
        目标['declared']=True#带上
    return 目标#目标

def 提供方目标标签(目标):#可见身份
    '同名则仅路由，否则 显示名 (路由)'
    路由=目标['provider'] if 'provider' in 目标 else None#路由
    显示=目标['displayName'] if 'displayName' in 目标 else None#显示名
    if 路由==显示:#同名
        return 路由#路由
    return f"{显示} ({路由})"#组合

def 提供方文案(模板,目标):#替换破坏性动作文案占位
    '{provider} → 目标标签'
    return 模板.replace('{provider}',提供方目标标签(目标))#替换

class 模型分区:#模型设置分区
    '一次一张编辑/装卡/创建卡；删除需确认'
    def __init__(自身,属性):#构造
        '记下 props 与本地 UI 态'
        自身.属性=属性
        自身.编辑中=None#当前编辑目标
        自身.添加中=False#添加休眠提供方
        自身.删除目标=None#待删目标
        自身.删除中=False#删除在飞
        自身.删除失败=None#删除失败
        自身.已保存目标=None#保存成功公告身份
        自身.声明中=False#自定义创建卡
        自身.已关装卡=set()#本会话关掉的装卡
        自身.编辑器实例=None#当前提供方编辑器
        自身.创建卡实例=None#自定义创建卡
        if isinstance(属性,dict) and 't' in 属性 and 'controller' in 属性 and 'api' in 属性 and 'useSnapshot' in 属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 读状态(自身):#读模型拼合快照
        '经 useSnapshot 选择器'
        用=自身.属性['useSnapshot']#选择器
        def 恒等(快照):
            '返回快照本身'
            return 快照#快照
        return 用(恒等)#快照

    def 公告已存(自身,目标):#保存后公告
        'reload 后再用目录里的新名字'
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        if 控制器 is None:#无
            自身.已保存目标=目标#直接
            return
        控制器.load()#刷新
        自身.已保存目标=目标#公告

    def 关编辑器(自身,已变,目标):#关编辑/添加/声明
        '清三态；变更则公告'
        自身.编辑中=None
        自身.添加中=False
        自身.声明中=False
        自身.编辑器实例=None
        自身.创建卡实例=None
        if 已变:#有变更
            自身.公告已存(目标)#公告

    def 关装卡(自身,已变,目标):#关首跑装卡
        '不碰其它卡片草稿'
        自身.已关装卡.add(目标['provider'])
        自身.编辑器实例=None
        if 已变:#有变更
            自身.公告已存(目标)#公告

    def 关删除(自身):#关删除对话框
        '删除在飞不可关'
        if 自身.删除中:#在飞
            return
        自身.删除目标=None
        自身.删除失败=None

    def 确认删除(自身):#执行删除
        '幂等；失败留对话框'
        if 自身.删除目标 is None or 自身.删除中:#不可
            return
        自身.删除中=True#在飞
        自身.删除失败=None
        接口=自身.属性['api']#api
        控制器=自身.属性['controller']#控制器
        失败=移除提供方档案(接口,控制器,自身.删除目标)#删
        if 失败 is not None:#失败
            自身.删除失败=失败
        else:#成功
            自身.删除目标=None#关
        自身.删除中=False#闲

    def 渲染提供方编辑器(自身,目标,命名空间,关闭):#共用编辑器投影
        '声明路由带 declared'
        状态=自身.读状态()#状态
        可写=状态['writable'] if 'writable' in 状态 else False#可写
        属性={#props
            'provider':目标['provider'],#路由
            'displayName':目标['displayName'] if 'displayName' in 目标 else None,#显示名
            'namespace':命名空间,#ns
            'settingsPath':目标['settingsPath'] if 'settingsPath' in 目标 else None,#路径
            'api':自身.属性['api'],#api
            't':自身.属性['t'],#文案
            'readOnly':not 可写,#只读
            'onClose':关闭,#关闭
        }#基础
        if 'declared' in 目标 and 目标['declared'] is True:#手声明
            属性['declared']=True#带上
        自身.编辑器实例=提供方编辑器(属性)#实例
        return 自身.编辑器实例#稍后绘制

    def 渲染(自身):#结构化视图
        '完整分区：行、装卡、添加、声明、删除确认'
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#文案
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        接口=自身.属性['api'] if 'api' in 自身.属性 else None#api
        if 控制器 is None or 接口 is None or 翻译 is None:#未注入
            return None#空
        状态=自身.读状态()#状态
        if 状态['status']=='idle':#尚未拉
            控制器.load()#首读
            状态=自身.读状态()#再读
        if 状态['status']=='error':#整页错误
            文=错误文案(状态['error']) if 'error' in 状态 and 状态['error'] is not None else None#去掉绝对路径后的失败句
            def 重试():#重试加载
                '再拉整页'
                控制器.load()#重试
            with 界面.column().classes('模型分区根 section'):
                if isinstance(文,str) and 文!='':
                    界面.label(翻译('loadFailed')+'：'+文)
                界面.button(翻译('retry'), on_click=重试)
            return
        行列表=状态['rows'] if 'rows' in 状态 and 状态['rows'] is not None else []#接合行
        命名空间图=状态['namespaces'] if 'namespaces' in 状态 and 状态['namespaces'] is not None else {}#ns 图
        def 取命名空间(名):#按名取 ns
            '命名空间图为 dict'
            return 命名空间图[名] if 名 in 命名空间图 else None#取
        已存行=None#保存公告行
        if 自身.已保存目标 is not None:#有公告
            已存路由=自身.已保存目标['provider'] if 'provider' in 自身.已保存目标 else None#路由
            for 行 in 行列表:#找
                条目=行['entry'] if 'entry' in 行 else None#条目
                if 条目 is not None and 'provider' in 条目 and 条目['provider']==已存路由:#匹配
                    已存行=行
                    break#找到
        if 已存行 is None:#目录尚未跟上
            已存身份=自身.已保存目标#身份
        else:#用目录新名字
            已存条目=已存行['entry'] if 'entry' in 已存行 else {}#条目
            已存身份={'provider':已存条目['provider'] if 'provider' in 已存条目 else None,'displayName':已存条目['displayName'] if 'displayName' in 已存条目 else None}#身份
        任一可用=any(提供方可用(行) for 行 in 行列表)#任一可用
        已配置=[行 for 行 in 行列表 if 'configured' in 行 and 行['configured']]#已配置行
        def 可添加行(行):#休眠可添加
            '未配置且有 ns'
            if 'configured' in 行 and 行['configured']:#已配置
                return False#否
            条目=行['entry'] if 'entry' in 行 else None#条目
            return 条目 is not None and 'settingsNs' in 条目 and 条目['settingsNs']!=''#有 ns
        可添加=[行 for 行 in 行列表 if 可添加行(行)]#可添加
        添加目标=自身.编辑中 if 自身.添加中 else None#添加目标
        添加命名空间=None if 添加目标 is None else 取命名空间(添加目标['settingsNs'] if 'settingsNs' in 添加目标 else None)#添加 ns
        协议列表=协议选项(取命名空间('llm-pi-ai'))#协议
        可写=状态['writable'] if 'writable' in 状态 else False#可写
        投影行=[]#行投影
        for 行 in 已配置:#已配置
            目标=编辑目标自(行)#目标
            命名空间=取命名空间(目标['settingsNs'] if 'settingsNs' in 目标 else None)#ns
            if 命名空间 is None:#无 ns
                continue#跳过
            路由=目标['provider'] if 'provider' in 目标 else None#路由
            if 需要装卡(行,任一可用) and 路由 not in 自身.已关装卡:#装卡
                def 关闭装卡(变,标=目标):#关装卡
                    '关闭首跑装卡'
                    自身.关装卡(变,标)#关
                投影行.append({#装卡行
                    'kind':'setup',#装卡
                    'provider':路由,#路由
                    'editor':自身.渲染提供方编辑器(目标,命名空间,关闭装卡),#编辑器
                })#装卡结束
                continue#下一
            条目=行['entry'] if 'entry' in 行 else {}#条目
            条目路由=条目['provider'] if 'provider' in 条目 else None#行路由
            打开=not 自身.添加中 and 自身.编辑中 is not None and 自身.编辑中['provider']==条目路由#打开
            凭证=行['credential'] if 'credential' in 行 else None#凭证
            凭证已配=凭证 is not None and 'configured' in 凭证 and 凭证['configured'] is True#已配
            环境=行['apiKeyEnv'] if 'apiKeyEnv' in 行 else None#环境
            凭证缺=not 凭证已配 and 环境 is not None and 凭证 is not None and 'configured' in 凭证 and 凭证['configured'] is False#缺
            可删='removable' in 行 and 行['removable']#可删
            def 点编辑(标=目标,开=打开):#编辑
                '打开或关闭该行编辑器'
                自身.已保存目标=None
                自身.声明中=False#清声明
                自身.添加中=False#清添加
                自身.编辑中=None if 开 else 标#切换
                自身.编辑器实例=None
                自身.创建卡实例=None
            def 点移除(标=目标):#移除
                '打开删除确认'
                自身.已保存目标=None
                自身.删除失败=None
                自身.删除目标=标#待删
            def 关闭编辑(变,标=目标):#关编辑器
                '关闭展开编辑器'
                自身.关编辑器(变,标)#关
            行面={#普通行
                'kind':'row',#行
                'provider':条目路由,#路由
                'displayName':条目['displayName'] if 'displayName' in 条目 else None,#显示名
                'customTag':翻译('customTag') if 'declared' in 条目 and 条目['declared'] is True else None,#自定义标
                'catalogError':错误文案(条目['error']) if 'error' in 条目 and isinstance(条目['error'],str) else None,#目录声明错误
                'credentialConfigured':凭证已配,#已配点
                'credentialMissing':凭证缺,#缺配点
                'credentialConfiguredLabel':翻译('credentialConfigured'),#已配文案
                'credentialMissingLabel':翻译('credentialMissing'),#缺配文案
                'editLabel':翻译('edit'),#编辑
                'editAria':提供方文案(翻译('editProvider'),目标),#编辑无障碍
                'onEdit':点编辑,#编辑
                'removeLabel':翻译('remove') if 可删 else None,#移除
                'removeAria':提供方文案(翻译('removeProvider'),目标) if 可删 else None,#移除无障碍
                'removeDisabled':not 可写,#移除禁用
                'onRemove':点移除 if 可删 else None,#移除
                'editor':自身.渲染提供方编辑器(目标,命名空间,关闭编辑) if 打开 else None,#展开编辑器
            }#行结束
            投影行.append(行面)#记入
        添加块=None#添加区
        if 添加目标 is not None and 添加命名空间 is not None:#添加卡
            def 关闭添加(变,标=添加目标):#关添加
                '关闭添加卡'
                自身.关编辑器(变,标)#关
            def 选提供方(值):#切换添加目标
                '按路由切到对应休眠行'
                def 匹配(行):#是否该路由
                    '目录路由相等'
                    条目=行['entry'] if 'entry' in 行 else {}#条目
                    return 'provider' in 条目 and 条目['provider']==值#匹配
                命中=None#行
                for 候选 in 可添加:#找
                    if 匹配(候选):#命中
                        命中=候选
                        break#找到
                自身.编辑中=编辑目标自(命中)#切换
                自身.编辑器实例=None
            添加编辑=提供方编辑器({#编辑器
                'provider':添加目标['provider'],#路由
                'displayName':添加目标['displayName'] if 'displayName' in 添加目标 else None,#显示名
                'hideTitle':True,#藏标题
                'namespace':添加命名空间,#ns
                'settingsPath':添加目标['settingsPath'] if 'settingsPath' in 添加目标 else None,#路径
                'api':接口,#api
                't':翻译,#文案
                'readOnly':not 可写,#只读
                'onClose':关闭添加,#关闭
            })#编辑器结束
            自身.编辑器实例=添加编辑
            选项=[]#选项
            for 候选 in 可添加:#可添加
                条目=候选['entry'] if 'entry' in 候选 else {}#条目
                选项.append({'value':条目['provider'] if 'provider' in 条目 else None,'label':条目['displayName'] if 'displayName' in 条目 else None})#选项
            添加块={#添加卡
                'kind':'add',#添加
                'providerLabel':翻译('provider'),#提供方标签
                'provider':添加目标['provider'],#当前
                'options':选项,#选项
                'onSelect':选提供方,#切换
                'editor':添加编辑,#编辑器
            }#添加结束
        elif 自身.声明中:#自定义创建
            def 关闭声明(变):#关创建卡
                '关闭自定义创建'
                自身.声明中=False
                自身.创建卡实例=None
                if 变:#已变更
                    控制器.load()#刷新
            占用=[]#占用路由
            for 候选 in 行列表:#已有
                条目=候选['entry'] if 'entry' in 候选 else {}#条目
                if 'provider' in 条目:#有路由
                    占用.append(条目['provider'])#占用
            pi命名空间=取命名空间('llm-pi-ai')#pi ns
            修订=pi命名空间['revision'] if pi命名空间 is not None and 'revision' in pi命名空间 else 0#修订
            自身.创建卡实例=自定义提供方卡片({#创建卡
                'taken':占用,#占用
                'protocols':协议列表,#协议
                'revision':修订,#修订
                'api':接口,#api
                't':翻译,#文案
                'readOnly':not 可写,#只读
                'onClose':关闭声明,#关闭
            })#创建结束
            添加块={'kind':'declare','card':自身.创建卡实例}#声明块
        else:#两个入口按钮
            def 点添加():#添加休眠提供方
                '打开添加卡'
                自身.已保存目标=None
                自身.声明中=False#清声明
                自身.添加中=True#添加
                自身.编辑中=编辑目标自(可添加[0]) if len(可添加)>0 else None#首个
                自身.创建卡实例=None
            def 点自定义():#声明自定义
                '打开自定义创建卡'
                自身.已保存目标=None
                自身.添加中=False#清添加
                自身.编辑中=None
                自身.声明中=True#声明
                自身.编辑器实例=None
            添加块={#入口
                'kind':'actions',#动作
                'addLabel':翻译('add'),#添加
                'addDisabled':len(可添加)==0 or not 可写,#禁用
                'onAdd':点添加,#添加
                'customLabel':翻译('customAdd'),#自定义
                'customDisabled':len(协议列表)==0 or not 可写,#禁用
                'onCustom':点自定义,#声明
            }#入口结束
        删除框=None#删除对话框
        if 自身.删除目标 is not None:#打开
            标=自身.删除目标#目标
            有凭证='credentialRef' in 标 and 标['credentialRef'] is not None#有凭证
            删述键='deleteDescriptionWithCredential' if 有凭证 else 'deleteDescription'#说明键
            删除框={#对话框
                'title':提供方文案(翻译('deleteTitle'),标),#标题
                'description':提供方文案(翻译(删述键),标),#说明
                'closeLabel':翻译('close'),#关闭
                'cancelLabel':翻译('cancel'),#取消
                'confirmLabel':提供方文案(翻译('deleting' if 自身.删除中 else 'deleteConfirm'),标),#确认
                'deleting':自身.删除中,#在飞
                'error':自身.删除失败,#失败
                'onClose':自身.关删除,#关
                'onConfirm':自身.确认删除,#确认
            }#对话框结束
        只读文=翻译('readOnly') if not 可写 and 状态['status']=='ready' else None#只读
        已存公告=提供方文案(翻译('savedProvider'),已存身份) if 已存身份 is not None else None#已存公告
        with 界面.column().classes('模型分区根 section'):
            界面.label(翻译('title')).classes('title')
            界面.label(翻译('intro')).classes('intro')
            if isinstance(只读文,str) and 只读文!='':
                界面.label(只读文).classes('notice')
            if isinstance(已存公告,str) and 已存公告!='':
                界面.label(已存公告).classes('savedNotice')
            for 行 in 投影行:
                if 行['kind']=='setup':
                    if 行['editor'] is not None:
                        行['editor'].渲染()
                    continue
                with 界面.column().classes('rowCard'):
                    名=行['displayName'] if isinstance(行['displayName'],str) and 行['displayName']!='' else ''
                    if 名=='' and 行['provider'] is not None:
                        名=str(行['provider'])
                    if 名!='':
                        界面.label(名)
                    if isinstance(行['customTag'],str) and 行['customTag']!='':
                        界面.label(行['customTag'])
                    if isinstance(行['catalogError'],str) and 行['catalogError']!='':
                        界面.label(行['catalogError'])
                    if 行['credentialConfigured']:
                        界面.label(行['credentialConfiguredLabel'])
                    if 行['credentialMissing']:
                        界面.label(行['credentialMissingLabel'])
                    界面.button(行['editLabel'], on_click=行['onEdit'])
                    if 行['onRemove'] is not None:
                        移除=界面.button(行['removeLabel'], on_click=行['onRemove'])
                        if 行['removeDisabled']:
                            移除.disable()
                    if 行['editor'] is not None:
                        行['editor'].渲染()
            if 添加块 is not None and 添加块['kind']=='add':
                选项={}
                for 项 in 添加块['options']:
                    值=项['value']
                    标签=项['label'] if isinstance(项['label'],str) and 项['label']!='' else str(值 if 值 is not None else '')
                    选项[值]=标签
                def 改选(事件):
                    '切换添加目标'
                    添加块['onSelect'](事件.value)
                界面.select(选项, value=添加块['provider'], label=添加块['providerLabel'], on_change=改选)
                if 添加块['editor'] is not None:
                    添加块['editor'].渲染()
            elif 添加块 is not None and 添加块['kind']=='declare':
                if 添加块['card'] is not None:
                    添加块['card'].渲染()
            elif 添加块 is not None and 添加块['kind']=='actions':
                加=界面.button(添加块['addLabel'], on_click=添加块['onAdd'])
                if 添加块['addDisabled']:
                    加.disable()
                自定=界面.button(添加块['customLabel'], on_click=添加块['onCustom'])
                if 添加块['customDisabled']:
                    自定.disable()
            if 删除框 is not None:
                with 界面.dialog() as 对话框:
                    with 界面.card():
                        界面.label(删除框['title'])
                        界面.label(删除框['description'])
                        if isinstance(删除框['error'],str) and 删除框['error']!='':
                            界面.label(删除框['error'])
                        界面.button(删除框['closeLabel'], on_click=删除框['onClose'])
                        界面.button(删除框['cancelLabel'], on_click=删除框['onClose'])
                        确认=界面.button(删除框['confirmLabel'], on_click=删除框['onConfirm'])
                        if 删除框['deleting']:
                            确认.disable()
                对话框.open()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

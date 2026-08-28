"""主题运行时：偏好、注册表、覆盖层与快照发布（无 DOM）。

对齐上游 `ui-theme/src/client/index.ts` 中 ThemeRuntime 核心逻辑。
公开面仅中文名。prefers-color-scheme 媒体查询由宿主注入系统色板。
"""
from ..主题设置 import 默认偏好,是否主题偏好,主题偏好字段#偏好约定

__all__=[#仅中文公开名
    '解析活动主题','合并令牌覆盖','主题运行时','内置主题','内置检视令牌','校验覆盖层',
]#公开面结束

内置主题=(#内置 light/dark
    {'id':'light','colorScheme':'light','tokens':{}},#浅
    {'id':'dark','colorScheme':'dark','tokens':{}},#深
)#结束

内置检视令牌=(#预定义可检视令牌目录（节选权威名，全文见上游）
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
    {'name':'--dsw-alias-state-success-primary','description':'Primary success state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-success-primary'},
    {'name':'--dsw-alias-state-warn-primary','description':'Primary warning state color.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-alias-state-warn-primary'},
    {'name':'--dsw-specific-sidebar-fill','description':'Sidebar column and title-row background.','valueType':'CSS color','requiresLightAndDark':True,'cssVariable':'--dsw-specific-sidebar-fill'},
)#结束

def 解析活动主题(偏好,主题们,系统色板='light'):#解析活动主题
    """system 经系统色板解析；返回活动主题定义。"""
    if not 是否主题偏好(偏好):#非法
        偏好=默认偏好#默认
    if 偏好=='system':#跟随
        目标=系统色板#系统
    else:#显式
        目标=偏好#light/dark
    for 主题 in 主题们:#按序
        if 主题.get('colorScheme')==目标 or 主题.get('id')==目标:#命中
            return 主题#活动
    return 主题们[0] if len(主题们)>0 else {'id':'default','colorScheme':目标,'tokens':{}}#回退

def 合并令牌覆盖(基础令牌,覆盖层们,色板):#合并令牌覆盖
    """按 seq 顺序，后层按令牌胜出；每个值按当前色板选取。"""
    结果=dict(基础令牌 or {})#拷贝
    for 覆盖 in 覆盖层们:#每层
        for 名,成对 in (覆盖 or {}).items():#令牌
            if isinstance(成对,dict):#成对
                值=成对.get(色板)#按色板
                if 值 is not None:#有
                    结果[名]=值#胜出
            elif isinstance(成对,str):#单值
                结果[名]=成对#写入
    return 结果#合并后

def 校验覆盖层(来源,令牌们):#校验并拷贝
    """裸字符串抛教学错误；必须 {light,dark} 字符串对。"""
    已校={}#防御拷贝
    for 名,值 in (令牌们 or {}).items():#逐令牌
        if isinstance(值,str):#裸串
            raise TypeError(f'theme override "{名}" from "{来源}" is a bare string — pass {{ light, dark }}')#教学
        if not isinstance(值,dict) or not isinstance(值.get('light'),str) or not isinstance(值.get('dark'),str):#形状
            raise TypeError(f'theme override "{名}" from "{来源}" must map to a {{ light, dark }} pair of strings')#教学
        已校[名]={'light':值['light'],'dark':值['dark']}#拷贝
    return 已校#已校

def 动态令牌(名):#登记时才见到的令牌
    """检视描述。"""
    项={'name':名,'description':'Theme token registered by the current Client composition.','valueType':'CSS value','requiresLightAndDark':True}#基
    if 名.startswith('--'):#CSS 变量
        项['cssVariable']=名#带上
    return 项#描述

class 主题运行时:#主题注册表与偏好所有者
    """light/dark 内置；第三方登记别名层覆盖。读取 getTheme；写入 setTheme。"""
    def __init__(自身,发出=None,宿主=None,系统深色=False):#构造
        """记下事件发出、设置作用域与初始系统色板。"""
        自身.发出=发出#theme/change
        自身.宿主=宿主#settings scope
        自身.主题们=[dict(t) for t in 内置主题]#登记表
        自身.偏好=默认偏好#偏好
        自身.修订=0#修订
        自身.覆盖层={}#source → {seq,tokens}
        自身.覆盖序号=0#下一 seq
        自身.系统深色=系统深色#matchMedia 投影
        自身.快照=自身.编快照()#初始
        if 宿主 is not None and hasattr(宿主,'subscribe'):#有作用域
            宿主.subscribe(自身.采纳)#订阅
        自身.采纳()#立刻采纳

    def 设系统深色(自身,深色):#宿主推送 OS 色板
        """偏好为 system 时重发。"""
        自身.系统深色=bool(深色)#写入
        if 自身.偏好=='system':#跟随
            自身.发布()#重发

    def 取主题(自身):#读快照
        """当前不可变快照。"""
        return 自身.快照#稳定引用

    def getTheme(自身):#英文别名
        """对齐上游 getTheme。"""
        return 自身.取主题()#转

    def 导出检视令牌(自身):#导出色板目录
        """稳定可 JSON 化的令牌描述。"""
        表={t['name']:dict(t) for t in 内置检视令牌}#内置
        for 主题 in 自身.主题们:#主题令牌
            for 名 in (主题.get('tokens') or {}):#名
                if 名 not in 表:#未见
                    表[名]=动态令牌(名)#动态
        for 层 in 自身.覆盖层.values():#覆盖
            for 名 in 层['tokens']:#名
                if 名 not in 表:#未见
                    表[名]=动态令牌(名)#动态
        return sorted(表.values(),key=lambda x:x['name'])#按名

    def 设主题(自身,标识):#切换偏好
        """未知 id 抛错；可持久偏好写作用域。"""
        if 标识!='system' and not any(t.get('id')==标识 for t in 自身.主题们):#未登记
            raise Exception(f'theme "{标识}" is not registered')#未知
        if 自身.偏好==标识:#无变
            return#空
        自身.偏好=标识#记下
        if 是否主题偏好(标识) and 自身.宿主 is not None:#可持久
            写=getattr(自身.宿主,'set',None)#写
            if callable(写):#有
                写(主题偏好字段,标识)#写
        自身.发布()#发布

    def setTheme(自身,标识):#英文别名
        """对齐上游 setTheme。"""
        return 自身.设主题(标识)#转

    def 采纳(自身):#从作用域拉
        """不写回。"""
        if 自身.宿主 is None:#无
            return#空
        取=getattr(自身.宿主,'getSnapshot',None)#快照
        if not callable(取):#无
            return#空
        段=取()#快照
        值=段.get('value') if isinstance(段,dict) else getattr(段,'value',None)#段
        if 值 is None:#缺
            return#空
        偏好=值.get('preference') if isinstance(值,dict) else getattr(值,'preference',None)#偏好
        if 偏好 is None or 自身.偏好==偏好:#一致
            return#空
        自身.偏好=偏好#采纳
        自身.发布()#发布

    def 登记(自身,定义):#登记主题
        """重复 id 抛错；返回拆除器。"""
        标识=定义.get('id')#id
        if 标识=='system':#不可登
            raise Exception('"system" is a preference, not a registrable theme id')#错
        if any(t.get('id')==标识 for t in 自身.主题们):#重复
            raise Exception(f'theme "{标识}" is already registered')#错
        自身.主题们=自身.主题们+[dict(定义)]#追加
        自身.发布()#发布
        def 拆除():#拆除
            """从表拿掉；若活动偏好被拆则回默认。"""
            if not any(t.get('id')==标识 for t in 自身.主题们):#已无
                return#空
            自身.主题们=[t for t in 自身.主题们 if t.get('id')!=标识]#滤
            if 自身.偏好==标识:#被拆
                自身.偏好=默认偏好#默认
            自身.发布()#发布
        return 拆除#拆除器

    def 覆盖令牌(自身,来源,令牌们):#叠覆盖层
        """同 source 再调整层替换重叠顶。"""
        层={'seq':自身.覆盖序号,'tokens':校验覆盖层(来源,令牌们)}#层
        自身.覆盖序号+=1#加序号
        自身.覆盖层[来源]=层#记下
        自身.发布()#发布
        def 拆除():#拆除本层
            """源已被重覆盖则空操作。"""
            if 自身.覆盖层.get(来源) is not 层:#已换
                return#空
            del 自身.覆盖层[来源]#删
            自身.发布()#发布
        return 拆除#拆除器

    def 编快照(自身):#编快照
        """按偏好与注册表编不可变快照。"""
        if 自身.偏好=='system':#跟随
            解析标识='dark' if 自身.系统深色 else 'light'#系统
        else:#显式
            解析标识=自身.偏好#原样
        活动=None#活动
        for t in 自身.主题们:#找
            if t.get('id')==解析标识:#命中
                活动=t#记下
                break#停
        if 活动 is None:#丢了
            raise Exception(f'theme registry lost "{解析标识}"')#错
        return {#快照
            'preference':自身.偏好,#偏好
            'active':自身.组合活动(活动),#组合
            'themes':[dict(t) for t in 自身.主题们],#表
            'revision':自身.修订,#修订
        }#结束

    def 组合活动(自身,活动):#折覆盖
        """无层则原样。"""
        if len(自身.覆盖层)==0:#无
            return dict(活动)#原样
        令牌=dict(活动.get('tokens') or {})#拷
        色板=活动.get('colorScheme')#色板
        for 层 in sorted(自身.覆盖层.values(),key=lambda x:x['seq']):#按 seq
            for 名,成对 in 层['tokens'].items():#令牌
                令牌[名]=成对[色板]#按色板
        结果=dict(活动)#拷
        结果['tokens']=令牌#组合
        return 结果#定义

    def 发布(自身):#递增并广播
        """递增修订并广播。"""
        自身.修订+=1#加一
        自身.快照=自身.编快照()#新快照
        if callable(自身.发出):#有
            自身.发出('theme/change',自身.快照)#发

import time#外部目录行的创建时刻
from ...工具.分块列表 import 追加分块列表,迭代分块列表,分块列表模式#分块列表

__all__=[#仅中文公开名
    '子智能体目录版本',
    '子智能体目录投影定义',
    '建立目录子体',
    '建立外部目录子体',
    '目录条目于状态',
]#公开面结束

子智能体目录版本=0#本地子创建写出的载荷版本
外部子智能体目录版本=2#外部执行写出的载荷版本

def _可选标签(数据):
    '有标签则必须是字符串'
    if 'label' not in 数据 or 数据['label'] is None:#没有
        return None#缺席
    if not isinstance(数据['label'],str):#类型不对
        raise ValueError('子智能体目录 label 必须是字符串')#拒绝
    return 数据['label']#标签

def _校验目录事件(数据):#校验一条目录事件
    'v0/v1 记本地模式，v1 另收 unknown，v2 记外部执行'
    if not isinstance(数据,dict):#须映射
        raise ValueError('子智能体目录事件必须是对象')#拒绝
    版本=数据['version'] if 'version' in 数据 else None#版本
    if 版本 not in (0,1,2):#已知版本
        raise ValueError('子智能体目录事件版本不匹配')#拒绝
    if 'childId' not in 数据 or not isinstance(数据['childId'],str):#子 id
        raise ValueError('子智能体目录事件需要 childId')#拒绝
    创建于=数据['childCreatedAt'] if 'childCreatedAt' in 数据 else None#创建时刻
    if not isinstance(创建于,int) or isinstance(创建于,bool) or 创建于<0:#非负 int
        raise ValueError('子智能体目录事件需要 childCreatedAt')#拒绝
    模式=数据['mode'] if 'mode' in 数据 else None#模式
    规范={'version':版本,'childId':数据['childId'],'childCreatedAt':创建于,'mode':模式}#公共字段
    if 模式=='continuable' and 版本 in (0,1):#可续跑
        标签=数据['label'] if 'label' in 数据 else None#标签
        if not isinstance(标签,str):#必须有
            raise ValueError('子智能体目录可续跑需要 label')#拒绝
        规范['label']=标签#标签
        return 规范#规范
    if 模式=='one-shot' and 版本 in (0,1):#一次性
        标签=_可选标签(数据)#可选
        if 标签 is not None:#有
            规范['label']=标签#标签
        return 规范#规范
    if 模式=='unknown' and 版本==1:#未知
        标签=_可选标签(数据)#可选
        if 标签 is not None:#有
            规范['label']=标签#标签
        return 规范#规范
    if 模式=='external' and 版本==2:#外部
        标签=_可选标签(数据)#可选
        if 标签 is not None:#有
            规范['label']=标签#标签
        return 规范#规范
    raise ValueError('子智能体目录事件 mode 不受支持')#拒绝

_头模式=分块列表模式(_校验目录事件)#头校验器

def 目录条目于状态(状态):#物化直接子行
    '按父目录事件顺序返回当前直接子行。状态为 dict'
    头=状态['head'] if 'head' in 状态 else None#分块头
    条目表=[]#累积
    for 数据 in 迭代分块列表(头):#插入序
        行={'id':数据['childId'],'createdAt':数据['childCreatedAt'],'mode':数据['mode']}#去掉版本与子字段名
        if 'label' in 数据:#有标签
            行['label']=数据['label']#标签
        条目表.append(行)#收下
    return 条目表#条目

def _目录初始(_头,继承事件计数):#投影初始
    '初始未见目录事实'
    return {'inheritedEventCount':继承事件计数}#仅继承计数

def _目录应用(状态,事件):#折叠一条事件
    '忽略非目录或继承前事件。状态与事件为 dict'
    if 'type' not in 事件 or 事件['type']!='subagent/catalog':#非目录
        return 状态#原样
    序号=事件['seq'] if 'seq' in 事件 else None#序号
    继承=状态['inheritedEventCount'] if 'inheritedEventCount' in 状态 else 0#继承计数
    if 序号 is not None and 序号<继承:#继承前
        return 状态#忽略
    头=状态['head'] if 'head' in 状态 else None#旧头
    规范=_校验目录事件(事件['data'] if 'data' in 事件 else None)#校验数据
    下一=dict(状态)#拷贝
    下一['head']=追加分块列表(头,规范)#新头
    return 下一#新状态

子智能体目录投影定义={#目录投影定义
    'key':'subagentCatalog',#投影键
    'schema':None,#公开视图模式（Python 侧不做 zod）
    'init':_目录初始,#初始
    'apply':_目录应用,#折叠
    'view':目录条目于状态,#视图
    'stateVersion':6,#状态版本
    'wire':{'view':目录条目于状态},#线视图
}#定义结束

def 建立目录子体(父,子头,描述符):#追加可续跑目录事实
    '把一条可续跑直接子发现事实追加到其父会话。父为会话；子头与描述符为 dict'
    子标识=子头['id'] if isinstance(子头,dict) else 子头.id#子 id
    创建于=子头['createdAt'] if isinstance(子头,dict) else 子头.createdAt#创建时刻
    父.追加('subagent/catalog',{#可续跑
        'version':子智能体目录版本,#版本
        'childId':子标识,#子 id
        'childCreatedAt':创建于,#创建时刻
        'mode':'continuable',#模式
        'label':描述符['label'],#标签
    })#追加结束

def 建立外部目录子体(父,子标识,标签):#追加外部目录事实
    '记录一次没有本地子会话的外部执行'
    父.追加('subagent/catalog',{#外部
        'version':外部子智能体目录版本,#版本
        'childId':子标识,#提供方返回的身份
        'childCreatedAt':int(time.time()*1000),#当前时刻
        'mode':'external',#外部
        'label':标签,#调用方标签
    })#追加结束

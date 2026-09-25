"""已校验偏好文档与确定性冲突解析；无浏览器依赖。"""
import json,re#文档解码与命令标识
from .绑定 import 规范化绑定,绑定键,Web绑定是否准入#绑定协议

__all__=[#仅中文公开名
    '命令标识模式','解析绑定','解析快捷键文档','绑定问题','解析快捷键默认',
    '有效快捷键','绑定重叠','编辑快捷键文档','解析快捷键编辑','解析快捷键定义',
]#公开面结束

命令标识模式=re.compile(r'^[a-z][a-zA-Z0-9-]*(?:\.[a-zA-Z][a-zA-Z0-9-]*)+$')#命令 id
配置模式=re.compile(r'^(desktop|web):(macos|windows|linux)$')#运行时:平台
合法修饰=frozenset(['primary','control','alt','shift','meta'])#修饰白名单
预留导航码=frozenset([#系统导航预留
    'Escape','Tab','Space','Backspace','Delete',
    'ArrowUp','ArrowDown','ArrowLeft','ArrowRight',
])#导航码结束
主修饰剪贴码=frozenset(['KeyC','KeyV','KeyX','KeyZ','KeyY','KeyQ','KeyH'])#主修饰剪贴等

def 是记录(值):
    """非空对象且非数组。"""
    return isinstance(值,dict)#映射即记录

def 解析绑定(值):
    """规范化前校验 JSON 绑定字段；拒绝未知字段以防有损重写。"""
    if 值 is None:#显式移除
        return None#解绑
    if not 是记录(值):#非对象
        raise ValueError('非法快捷键绑定')#拒绝
    for 键 in 值:#未知字段
        if 键 not in ('code','secondCode','modifiers'):#仅允许三字段
            raise ValueError('非法快捷键绑定')#拒绝
    if not isinstance(值.get('code'),str) or not isinstance(值.get('modifiers'),list):#类型
        raise ValueError('非法快捷键绑定')#拒绝
    if 'secondCode' in 值 and not isinstance(值['secondCode'],str):#次码类型
        raise ValueError('非法快捷键绑定')#拒绝
    for 修饰 in 值['modifiers']:#逐修饰
        if not isinstance(修饰,str) or 修饰 not in 合法修饰:#非法
            raise ValueError('非法快捷键绑定')#拒绝
    绑定={'code':值['code'],'modifiers':list(值['modifiers'])}#可序列化绑定
    if isinstance(值.get('secondCode'),str):#有次码
        绑定['secondCode']=值['secondCode']#写入
    规范化绑定(绑定,'windows')#用 Windows 校验物理码
    return 绑定#返回

def 解析快捷键文档(原始):
    """解码完整文档，保留休眠命令覆盖；失败返回 'invalid' 或 'future'。"""
    if 原始 is None:#缺失文档
        return {'schemaVersion':1,'profiles':{}}#空文档
    try:#解析 JSON 与字段
        值=json.loads(原始)#解码
        if not 是记录(值):#根须对象
            return 'invalid'#非法
        版本=值.get('schemaVersion')#版本
        if isinstance(版本,int) and 版本>2:#未来版本
            return 'future'#未来
        if 版本 not in (1,2) or not 是记录(值.get('profiles')):#版本或 profiles
            return 'invalid'#非法
        for 键 in 值:#未知根字段
            if 键 not in ('schemaVersion','profiles'):#仅允许两字段
                return 'invalid'#非法
        配置表={}#已接受 profiles
        for 配置名,覆盖 in 值['profiles'].items():#逐配置
            if 配置模式.match(配置名) is None or not 是记录(覆盖):#形态
                return 'invalid'#非法
            绑定表={}#本配置覆盖
            for 标识,候选项 in 覆盖.items():#逐命令
                if 命令标识模式.match(标识) is None:#非法 id
                    return 'invalid'#非法
                已解析=解析绑定(候选项)#解析绑定
                if 版本==1 and 已解析 is not None and 已解析.get('secondCode') is not None:#v1 拒和弦
                    return 'invalid'#非法
                绑定表[标识]=已解析#写入
            配置表[配置名]=绑定表#写入配置
        return {'schemaVersion':版本,'profiles':配置表}#已接受
    except (json.JSONDecodeError,ValueError,TypeError):#非法 JSON 或绑定
        return 'invalid'#保留原文档语义：调用方不改写

def 绑定问题(绑定,运行时,平台):
    """用展开后的物理修饰键检查系统/编辑器/浏览器预留；允许时为 None。"""
    码=绑定['code']#物理码
    修饰=绑定['modifiers']#修饰列
    if 运行时=='desktop' and (平台=='windows' or 平台=='macos'):#桌面宽平台
        return None#桌面不拒
    if 绑定.get('secondCode') is not None:#和弦
        return 'unsupported-key'#不支持键
    if len(修饰)==0 or all(项=='shift' for 项 in 修饰):#无修饰或仅 Shift
        return 'modifier-required'#需要修饰
    if (平台=='windows' or 平台=='macos') and len(修饰)>=3:#三修饰以上
        return None#放行
    if 运行时=='web' and (平台=='windows' or 平台=='macos') and Web绑定是否准入(绑定,平台):#Web 白名单
        return None#放行
    含主='meta' in 修饰 if 平台=='macos' else 'control' in 修饰#是否含主修饰
    if 码 in 预留导航码:#导航预留
        return 'reserved'#预留
    if 码=='Enter' and 'alt' not in 修饰:#Enter 非 Alt
        return 'reserved'#预留
    if 含主 and 码 in 主修饰剪贴码:#剪贴等
        return 'reserved'#预留
    if 含主 and 码=='KeyA' and 'shift' not in 修饰:#全选
        return 'reserved'#预留
    if 平台!='macos' and ('meta' in 修饰 or ('alt' in 修饰 and 码 in ('F4','F2'))):#非 Mac 系统
        return 'reserved'#预留
    if 平台=='macos' and 'control' in 修饰 and 'meta' in 修饰:#Ctrl+Cmd
        return 'reserved'#预留
    if 平台=='macos' and 'alt' in 修饰 and not 含主:#仅 Option
        return 'reserved'#预留
    if 运行时=='web' and not Web绑定是否准入(绑定,平台):#Web 未准入
        return 'unsupported-browser'#浏览器不支持
    return None#通过

def 解析快捷键默认(定义,运行时,平台):
    """选取命令所有者对某一设备配置的显式默认。"""
    return 定义['defaults'].get(运行时+':'+平台)#配置键

def 绑定重叠(左,右):
    """检测相同组合，或单键是否落在双键和弦内。"""
    if '+'.join(左['modifiers'])!='+'.join(右['modifiers']):#修饰不同
        return False#不重叠
    if 左.get('secondCode') is not None and 右.get('secondCode') is not None:#双方和弦
        return 绑定键(左)==绑定键(右)#全等索引
    for 码 in (左['code'],左.get('secondCode')):#左的每个码
        if 码 is not None and (码==右['code'] or 码==右.get('secondCode')):#落在右内
            return True#重叠
    return False#不重叠

def 有效快捷键(定义表,文档,运行时,平台):
    """与注册顺序无关地解析覆盖与冲突；显式覆盖挤掉默认。"""
    覆盖=文档['profiles'].get(运行时+':'+平台) or {}#本配置覆盖
    #固定预留行
    固定行=[]#固定绑定行
    for 行 in 定义表:#逐定义
        固定=行.get('fixed')#可选固定
        if 固定 is None:#非固定
            continue#跳过
        for 候选项 in 固定:#逐绑定
            固定行.append({'id':行['id'],'binding':规范化绑定(候选项,平台)})#规范
    #可编辑行
    行表=[]#有效行草稿
    for 行 in 定义表:#逐定义
        if 行.get('fixed') is not None:#固定不进可编辑
            continue#跳过
        标识=行['id']#命令 id
        已改=标识 in 覆盖#显式覆盖
        if 已改:#用覆盖
            候选=覆盖[标识]#可为 None
        else:#用默认
            候选=解析快捷键默认({'id':标识,'defaults':行['defaults']},运行时,平台)#默认
        if 候选 is None:#未绑
            绑定=None#空
        else:#有候选
            绑定=规范化绑定(候选,平台)#规范
        问题=None if 绑定 is None else 绑定问题(绑定,运行时,平台)#问题
        行表.append({'id':标识,'binding':绑定,'modified':已改,'issue':问题})#草稿
    #补冲突
    结果=[]#最终行
    for 行 in 行表:#逐行算冲突
        绑定=行['binding']#本绑定
        if 绑定 is None:#未绑无冲突
            冲突=[]#空
        else:#收集冲突 id
            冲突集合=[]#有序去重
            已见=set()#去重集
            for 他 in 行表:#与其他可编辑
                if 他['id']==行['id']:#自身
                    continue#跳过
                if 他['binding'] is None or 他['issue'] is not None:#无效他行
                    continue#跳过
                if not 绑定重叠(他['binding'],绑定):#不重叠
                    continue#跳过
                #本未改或他已改才记冲突（显式覆盖不挤未改默认）
                if (not 行['modified']) or 他['modified']:#准入冲突
                    if 他['id'] not in 已见:#未见
                        已见.add(他['id'])#记
                        冲突集合.append(他['id'])#追加
            for 他 in 固定行:#与固定
                if 绑定重叠(他['binding'],绑定):#重叠
                    if 他['id'] not in 已见:#未见
                        已见.add(他['id'])#记
                        冲突集合.append(他['id'])#追加
            冲突=冲突集合#定稿
        结果.append({#有效行
            'id':行['id'],
            'binding':绑定,
            'modified':行['modified'],
            'conflicts':冲突,
            'issue':行['issue'],
        })#行结束
    return 结果#全部活跃命令

def 编辑快捷键文档(文档,编辑,运行时,平台):
    """应用编辑，不改其他配置或休眠覆盖。"""
    if 运行时=='desktop' and (平台=='macos' or 平台=='windows'):#桌面宽平台升 v2
        版本=2#schema v2
    else:#其余保留
        版本=文档['schemaVersion']#原版本
    配置名=运行时+':'+平台#当前配置
    覆盖=dict(文档['profiles'].get(配置名) or {})#浅拷覆盖
    类型=编辑['type']#编辑类型
    if 类型=='set':#设置或解绑
        覆盖[编辑['id']]=编辑['binding']#写入
    elif 类型=='reset':#清单条覆盖
        覆盖.pop(编辑['id'],None)#删除
    elif 类型=='reset-all':#清本配置
        覆盖={}#空
    else:#闭包外
        raise ValueError('非法快捷键编辑')#拒绝
    配置表=dict(文档['profiles'])#浅拷 profiles
    配置表[配置名]=覆盖#写回
    return {'schemaVersion':版本,'profiles':配置表}#候选文档

def 解析快捷键编辑(值):
    """在 Desktop IPC 边界校验偏好编辑。"""
    if not 是记录(值):#非对象
        raise ValueError('非法快捷键编辑')#拒绝
    if 值.get('type')=='reset-all' and len(值)==1:#全重置
        return {'type':'reset-all'}#编辑
    if not isinstance(值.get('id'),str) or 命令标识模式.match(值['id']) is None:#命令 id
        raise ValueError('非法快捷键命令')#拒绝
    if 值.get('type')=='reset' and len(值)==2:#重置一条
        return {'type':'reset','id':值['id']}#编辑
    if 值.get('type')=='set' and len(值)==3:#设置
        return {'type':'set','id':值['id'],'binding':解析绑定(值.get('binding'))}#编辑
    raise ValueError('非法快捷键编辑')#拒绝

def 解析快捷键定义(值):
    """在 IPC 入口校验受信产品可序列化命令目录。"""
    if not isinstance(值,list):#须数组
        raise ValueError('非法快捷键目录')#拒绝
    标识集=set()#已见 id
    for 条目 in 值:#逐条
        if not 是记录(条目):#非对象
            raise ValueError('非法快捷键定义')#拒绝
        标识=条目.get('id')#id
        if not isinstance(标识,str) or 命令标识模式.match(标识) is None or 标识 in 标识集:#重复或非法
            raise ValueError('非法快捷键定义')#拒绝
        if not 是记录(条目.get('defaults')):#defaults
            raise ValueError('非法快捷键定义')#拒绝
        for 键 in 条目:#未知字段
            if 键 not in ('id','defaults','fixed'):#仅允许
                raise ValueError('非法快捷键定义')#拒绝
        标识集.add(标识)#登记
        if 'fixed' in 条目:#固定定义
            固定=条目['fixed']#固定列
            if not isinstance(固定,list) or len(固定)==0 or len(条目['defaults'])>0:#形态
                raise ValueError('非法固定快捷键定义')#拒绝
            for 候选项 in 固定:#逐绑定
                if 解析绑定(候选项) is None:#不可为 null
                    raise ValueError('非法固定快捷键绑定')#拒绝
        for 配置名,候选 in 条目['defaults'].items():#逐默认
            if 配置模式.match(配置名) is None:#非法配置
                raise ValueError('非法快捷键配置')#拒绝
            if 解析绑定(候选) is None:#默认不可 null
                raise ValueError('非法快捷键默认')#拒绝
    #跨配置冲突与预留
    for 运行时 in ('desktop','web'):#双壳
        for 平台 in ('macos','windows','linux'):#三平台
            已绑=[]#已规范默认
            for 条目 in 值:#逐定义
                候选项=解析快捷键默认(条目,运行时,平台)#默认
                if 候选项 is None:#无默认
                    continue#跳过
                规范=规范化绑定(候选项,平台)#规范
                for 他 in 已绑:#与已有
                    if 绑定重叠(他,规范):#冲突
                        raise ValueError('冲突或预留的快捷键默认')#拒绝
                if 绑定问题(规范,运行时,平台) is not None:#预留
                    raise ValueError('冲突或预留的快捷键默认')#拒绝
                已绑.append(规范)#登记
    return 值#已校验定义表

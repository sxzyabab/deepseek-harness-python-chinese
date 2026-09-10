"""已发布 v2 逻辑产物校验与当代恢复。"""
import json,os#JSON与绝对路径
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    会话格式计数,#格式计数
    会话格式安全整数,#安全整数
)#从会话格式导入
from ..会话格式_v0到v1 import 断言已发布产物关系#从v0到v1导入
from .处置 import 已发布v2事件处置,已发布v2事件类型#从处置导入

头必填=('version','id','createdAt','isSeeded','delegationDepth')#头必填
头可选=('cwd','parentSession','origin','agentPreset')#头可选
事件必填=('type','seq','time','data')#事件必填
表面类型=frozenset(['user/message','assistant/message','tool/result'])#表面类型
表面可选=('ignorable','sourceEventSeqs','surfaceOp')#表面可选
日志可选=('ignorable',)#日志可选
已发布v2事件类型集=frozenset(已发布v2事件类型)#v2类型集
已发布v2关系扩展={#关系扩展
    'stepEvents':frozenset(['assistant/attempt']),#步骤事件
    'preservedSourceTitleRequestText':True,#保留标题请求文本
}#扩展结束

def 断言已发布v2头(头):#断言v2头
    """校验已发布 v2 写出的精确逻辑头。"""
    记录=json记录(头,'format v2 header')#记录
    精确键(记录,头必填,头可选,'format v2 header')#精确键
    if 记录['version']!=2:#版本
        raise 会话格式错误('expected format v2 header')#版本
    if not isinstance(记录['id'],str):#id
        raise 会话格式错误('format v2 header id must be a string')#id
    会话格式计数(记录['createdAt'],'format v2 header createdAt')#创建时间
    会话格式计数(记录['delegationDepth'],'format v2 header delegationDepth')#委托深度
    if not isinstance(记录['isSeeded'],bool):#种子
        raise 会话格式错误('format v2 header isSeeded must be boolean')#种子
    if 'cwd' in 记录 and (not isinstance(记录['cwd'],str) or not os.path.isabs(记录['cwd'])):#cwd非法
        raise 会话格式错误('format v2 header cwd must be absolute')#错误
    for 键 in ('parentSession','agentPreset'):#可选字符串
        if 键 in 记录 and not isinstance(记录[键],str):#类型不符
            raise 会话格式错误(f'format v2 header {键} must be a string')#错误
    if 'origin' in 记录 and 记录['origin']!='subagent':#origin非法
        raise 会话格式错误('format v2 header origin must be "subagent"')#错误

def 断言已发布v2产物(产物):#断言v2产物
    """校验已发布 v2 写出器发出的精确逻辑镜像。"""
    校验已发布v2产物(产物,'current',已发布v2事件类型集)#当代+已发布类型

def 断言已发布v2物理产物(产物):#断言物理产物
    """仅校验已发布 v2 物理头、事件信封与继承切割。"""
    校验已发布v2产物(产物,'physical')#物理模式

def 校验已发布v2产物(产物,模式,已知事件类型=None,关系头版本=None):#校验v2产物
    """按当代或物理模式校验产物。"""
    if 关系头版本 is None:#默认用产物头版本
        关系头版本=产物['header']['version']#关系头版本
    断言已发布v2头(产物['header'])#断言头
    切割=会话格式计数(产物['inheritedEventCount'],'format v2 inherited event count')#切割
    if 切割>len(产物['events']):#越界
        raise 会话格式错误('format v2 inherited event count exceeds its events')#越界
    if not 产物['header']['isSeeded'] and 切割!=0:#非种子
        raise 会话格式错误('unseeded format v2 Session has inherited events')#非种子
    最后继承标记=None#最后继承标记
    for 下标,事件 in enumerate(产物['events']):#遍历事件
        记录=json记录(事件,f'format v2 event {下标}')#记录
        类型=记录['type']#类型
        if not isinstance(类型,str):#类型须串
            raise 会话格式错误(f'format v2 event {下标} type must be a string')#类型须串
        处置=已发布v2事件处置.get(类型)#处置
        已安装=已知事件类型 is not None and 类型 in 已知事件类型#已安装
        可忽略未知=处置 is None and 记录.get('ignorable') is True#可忽略未知
        if 模式=='current' and 处置 is None and not 已安装 and not 可忽略未知:#未知必填
            raise 会话格式不支持迁移错误(#拒绝
                f'format v2 contains unknown event type {json.dumps(类型,ensure_ascii=False)} at seq {下标}',#消息
            )#Error结束
        表面=处置 is not None and 类型 in 表面类型#是否表面
        if 模式=='physical' or 处置 is None:#物理或未知
            可选=表面可选#表面可选
        elif 表面:#表面
            可选=表面可选#表面可选
        else:#日志
            可选=日志可选#日志可选
        精确键(记录,事件必填,可选,f'format v2 event {下标}')#精确键
        if 记录['seq']!=下标:#非稠密
            raise 会话格式错误(f'format v2 event {下标} is not dense')#非稠密
        会话格式安全整数(记录['time'],f'format v2 event {下标} time')#时间
        if 'ignorable' in 记录 and 记录['ignorable'] is not True:#ignorable非法
            raise 会话格式错误(f'format v2 event {下标} ignorable must be true when present')#错误
        if 类型=='session/end-seed':#end-seed
            数据=json记录(事件['data'],f'session/end-seed {下标} data')#data
            if 数据.get('inherited') is True:#继承标记
                最后继承标记=下标#记下
    if 产物['header']['isSeeded'] and 最后继承标记!=切割:#种子不一致
        raise 会话格式错误('format v2 seeded header disagrees with its last inherited end-seed marker')#错误
    if not 产物['header']['isSeeded'] and 最后继承标记 is not None:#非种子却有标记
        raise 会话格式错误('format v2 unseeded Session contains an inherited end-seed marker')#错误
    if 模式=='current':#当代模式：按关系头版本做关系校验
        断言已发布产物关系(#关系
            {**产物,'header':{**产物['header'],'version':关系头版本}},#关系头版本
            已发布v2关系扩展,#扩展
        )#关系结束

def json记录(值,标签):#JSON记录
    """要求值为非 null 非数组对象。"""
    if not isinstance(值,dict):#非对象
        raise 会话格式错误(f'{标签} must be an object')#错误
    return 值#断言

def 精确键(值,必填,可选,标签):#精确键
    """要求恰好含必填键，且无意外键。"""
    允许=set(必填)|set(可选)#允许集
    for 键 in 必填:#缺键
        if 键 not in 值:#缺键
            raise 会话格式错误(f'{标签} lacks required field {键}')#缺键错误
    for 键 in 值.keys():#意外键
        if 键 not in 允许:#意外
            raise 会话格式错误(f'{标签} has unexpected field {键}')#意外错误

def 恢复已发布v2产物(产物,已知事件类型,关系头版本=None):#恢复v2产物
    """恢复并校验一个已解码的已发布 v2 产物。"""
    if 关系头版本 is None:#默认用产物头版本
        关系头版本=产物['header']['version']#关系头版本
    校验已发布v2产物(产物,'current',已知事件类型,关系头版本)#当代模式
    return 产物#返回

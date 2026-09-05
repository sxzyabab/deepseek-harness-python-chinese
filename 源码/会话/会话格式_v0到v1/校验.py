"""已发布 v0 与 v1 共享布局的头、坐标与载荷校验。"""
import json#诊断序列化
import os#绝对路径判定
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    会话格式计数,#格式计数
    会话格式安全整数,#安全整数
    快照会话格式json,#快照JSON
)#从会话格式导入
from .处置 import 已发布v0事件处置表#从处置导入
from .载荷校验 import 断言已发布载荷语义#从载荷校验导入
from .关系 import 断言已发布产物关系#从关系导入
from .校验辅助 import 断言已发布v0键,已发布v0记录#从辅助导入

头必填=('version','id','createdAt','isSeeded','delegationDepth')#头必填
头可选=('cwd','parentSession','origin','agentPreset')#头可选
事件必填=('type','seq','time','data')#事件必填
表面事件类型=frozenset(['user/message','assistant/message','tool/result'])#表面类型
表面可选=('ignorable','sourceEventSeqs','surfaceOp')#表面可选
日志可选=('ignorable',)#日志可选
遗留源类型=frozenset(['steering/message','request/header-delta','mode/set'])#遗留源类型
已发布v0事件类型集=frozenset(已发布v0事件处置表.keys())#v0类型集

def 断言已发布会话格式头(头,版本):#断言会话格式头
    """校验已发布 v0 与 v1 共享的逻辑头。"""
    记录=已发布v0记录(头,f'format v{版本} header')#记录
    断言已发布v0键(记录,头必填,头可选,f'format v{版本} header')#精确键
    if 记录['version']!=版本:#版本
        raise 会话格式错误(f'expected format v{版本} header')#版本
    if not isinstance(记录['id'],str):#id
        raise 会话格式错误(f'format v{版本} header id must be a string')#id
    会话格式计数(记录['createdAt'],f'format v{版本} header createdAt')#创建时间
    if not isinstance(记录['isSeeded'],bool):#种子类型
        raise 会话格式错误(f'format v{版本} header isSeeded must be a boolean')#错误
    会话格式计数(记录['delegationDepth'],f'format v{版本} header delegationDepth')#委托深度
    for 键 in ('cwd','parentSession','agentPreset'):#可选字符串
        if 键 in 记录 and not isinstance(记录[键],str):#类型不符
            raise 会话格式错误(f'format v{版本} header {键} must be a string')#错误
    if isinstance(记录.get('cwd'),str) and not os.path.isabs(记录['cwd']):#cwd非绝对
        raise 会话格式错误(f'format v{版本} header cwd must be absolute')#错误
    if 'origin' in 记录 and 记录['origin']!='subagent':#origin非法
        raise 会话格式错误(f'format v{版本} header origin must be "subagent"')#错误

def 断言已发布v1头(头):#断言v1头
    """校验一个已发布 v1 逻辑头。"""
    断言已发布会话格式头(头,1)#委托共享校验

def 断言已发布v0源产物(产物):#断言v0源产物
    """在历史规范化器运行前校验 v0。"""
    断言已发布会话格式头(产物['header'],0)#断言头
    断言产物坐标(产物,True,已发布v0事件类型集)#断言坐标

def 断言规范化已发布v0产物(产物):#断言规范化v0
    """在身份头版本变更前校验已规范化的 v0 事件。"""
    断言已发布会话格式头(产物['header'],0)#断言头
    断言产物坐标(产物,False,已发布v0事件类型集)#断言坐标
    for 事件 in 产物['events']:#遍历事件
        断言已发布事件载荷(事件,0)#断言载荷
    断言已发布产物关系(产物)#断言关系

def 断言已发布v1产物(产物):#断言v1产物
    """校验已发布 v1 写出器发出的精确逻辑镜像。"""
    断言已发布v1头(产物['header'])#断言头
    断言产物坐标(产物,False,已发布v0事件类型集)#断言坐标
    for 事件 in 产物['events']:#遍历事件
        if 事件['type'] in 已发布v0事件处置表:#已知则断言载荷
            断言已发布事件载荷(事件,1)#断言载荷
    断言已发布产物关系(产物)#断言关系

def 恢复已发布v1产物(产物,已知事件类型):#恢复v1产物
    """相对已安装构建的普通事件词表恢复 v1，不冻结载荷增补。"""
    断言已发布v1头(产物['header'])#断言头
    断言产物坐标(产物,False,已知事件类型)#断言坐标
    return 产物#返回

def 断言已发布v1物理产物(产物):#断言v1物理产物
    """校验已发布 v1 物理布局而不解释事件词表。"""
    断言已发布v1头(产物['header'])#断言头
    断言产物坐标(产物,False,None,True)#词表中立坐标

def 断言产物坐标(产物,允许遗留steering,已知事件类型=None,词表中立=False):#断言产物坐标
    """校验产物继承数与稠密事件坐标。"""
    继承事件数=会话格式计数(产物['inheritedEventCount'],'Session inheritedEventCount')#继承数
    if 继承事件数>len(产物['events']):#越界
        raise 会话格式错误('Session inheritedEventCount exceeds its event count')#错误
    if not 产物['header']['isSeeded'] and 继承事件数!=0:#非种子却有继承
        raise 会话格式错误('unseeded Session inheritedEventCount must be 0')#错误
    for 下标 in range(len(产物['events'])):#遍历事件
        事件=产物['events'][下标]#事件
        记录=已发布v0记录(事件,f'Session event {下标}')#记录
        类型=记录['type']#类型
        if not isinstance(类型,str):#类型须串
            raise 会话格式错误(f'Session event {下标} type must be a string')#类型须串
        处置=已发布v0事件处置表.get(类型)#处置
        遗留=允许遗留steering and 类型 in 遗留源类型#是否遗留
        当前已知=已知事件类型 is not None and 类型 in 已知事件类型#是否已知
        可忽略当代=(not 允许遗留steering) and (not 当前已知) and 记录.get('ignorable') is True#可忽略当代
        if (not 当前已知) and (not 遗留) and (not 可忽略当代) and (not 词表中立):#未知必填
            if 允许遗留steering:#历史源
                raise 会话格式不支持迁移错误(#拒绝
                    f'format v0 contains unknown historical event type {json.dumps(类型,ensure_ascii=False)} at seq {下标}; migration refuses unknown historical events even when ignorable',#消息
                )#Error结束
            raise 会话格式不支持迁移错误(#拒绝
                f'format v1 contains unknown required event type {json.dumps(类型,ensure_ascii=False)} at seq {下标}',#消息
            )#Error结束
        冻结信封=(not 词表中立) and 已知事件类型 is 已发布v0事件类型集#冻结信封
        表面=类型 in 表面事件类型 if 处置 is not None else 类型=='steering/message'#是否表面
        if 冻结信封:#冻结时按表面或日志
            可选=表面可选 if 表面 else 日志可选#可选键
        else:#非冻结用表面可选
            可选=表面可选#表面可选
        断言已发布v0键(记录,事件必填,可选,f'Session event {下标}')#精确键
        if 记录['seq']!=下标:#非稠密
            raise 会话格式错误(f'Session event {下标} has non-dense seq {json.dumps(记录["seq"],ensure_ascii=False)}')#错误
        会话格式安全整数(记录['time'],f'Session event {下标} time')#时间
        if 记录.get('ignorable') is not None and 记录.get('ignorable') is not True:#ignorable非法
            raise 会话格式错误(f'Session event {下标} ignorable must be true when present')#错误
        if 冻结信封 and 表面:#表面元数据
            断言已发布表面元数据(记录,下标,类型,'allow-empty-assistant')#表面元数据

def 断言已发布表面元数据(记录,序号,类型,助手出处):#断言表面元数据
    """校验一个已发布代际的共享布局表面引用。"""
    出处们=记录.get('sourceEventSeqs')#出处列表
    if 类型=='assistant/message' and 出处们 is not None and 助手出处=='forbid-assistant':#禁止出处
        raise 会话格式错误(f'assistant/message {序号} retains obsolete chunk provenance')#错误
    if 出处们 is not None:#有出处
        if not isinstance(出处们,list):#须数组
            raise 会话格式错误(f'{类型} {序号} sourceEventSeqs must be an array')#须数组
        已见=set()#已见
        for 出处 in 出处们:#遍历出处
            当前=会话格式计数(出处,f'{类型} {序号} sourceEventSeqs member')#成员
            if 当前>=序号 or 当前 in 已见:#非法
                raise 会话格式错误(f'{类型} {序号} sourceEventSeqs must be unique earlier seqs')#错误
            已见.add(当前)#记入
        if len(出处们)==0 and (类型!='assistant/message' or 助手出处=='forbid-assistant'):#空且不允许
            raise 会话格式错误(f'{类型} {序号} sourceEventSeqs must be non-empty')#错误
    操作=记录.get('surfaceOp')#表面操作
    if 操作 is None or 操作=='append':#无或追加
        return#结束
    替换=已发布v0记录(操作,f'{类型} {序号} surfaceOp')#替换记录
    断言已发布v0键(替换,['op','start','end'],[],f'{类型} {序号} surfaceOp')#精确键
    if 替换['op']!='replace':#须替换
        raise 会话格式错误(f'{类型} {序号} surfaceOp must replace')#须替换
    起点=会话格式计数(替换['start'],f'{类型} {序号} surface start')#起点
    终点=会话格式计数(替换['end'],f'{类型} {序号} surface end')#终点
    if 起点>=序号 or 终点>=序号:#非法替换
        raise 会话格式错误(f'{类型} {序号} has an invalid surface replacement')#非法替换

def 断言已发布事件载荷(事件,版本):#断言事件载荷
    """在遗留规范化后校验一个精确已知载荷。"""
    处置=已发布v0事件处置表.get(事件['type'])#处置
    if 处置 is None:#未知类型
        raise 会话格式不支持迁移错误(#拒绝
            f'format v0 contains unknown event type {json.dumps(事件["type"],ensure_ascii=False)} at seq {事件["seq"]}',#消息
        )#Error结束
    数据=已发布v0记录(事件['data'],f'{事件["type"]} {事件["seq"]} data')#data
    if 事件['type']=='subagent/descriptor' and 数据.get('version')!=3:#描述符非v3
        描述符版本=会话格式计数(数据['version'],f'{事件["type"]} {事件["seq"]} version')#描述符版本
        if 版本==0:#v0拒绝
            raise 会话格式不支持迁移错误(#拒绝
                f'{事件["type"]} {事件["seq"]} uses unsupported descriptor version {描述符版本}',#消息
            )#Error结束
        return#v1放行非v3
    if 版本==1 and 事件['type']=='session-log-deepseek/delivery-accepted':#版本可选
        版本可选=list(处置['optional'])+['sessionFormatVersion']#补版本字段
    else:#原可选
        版本可选=处置['optional']#原可选
    断言已发布v0键(数据,处置['required'],版本可选,f'{事件["type"]} {事件["seq"]} data')#精确键
    for 键 in 处置['opaque']:#不透明键
        if 键 in 数据:#有该键
            快照会话格式json(数据[键],f'{事件["type"]} {事件["seq"]} opaque {键}')#快照
    断言已发布载荷语义(事件,版本)#载荷语义

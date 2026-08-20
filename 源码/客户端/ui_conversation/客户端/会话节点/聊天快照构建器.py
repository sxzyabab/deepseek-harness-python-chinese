"""把聊天视图节点增量折成 ChatSnapshot。

对齐上游 `ui-conversation/src/client/conversation-nodes/chat-snapshot-builder.ts`。公开面仅中文名。
按键存储、位置索引与遗留兼容切片。
"""
from ..约定.聊天节点 import 运行中工具#运行中谓词
from .面辅助 import 取字段#字段

__all__=['聊天快照构建器','聊天视图定义','登记聊天会话视图']#仅中文公开名

空键=()#空 key 列表
空回合=()#空回合号
空列表=()#空只读列表

def 同引用(左,右):#两列表是否同长度且逐项引用相等
    """长度与每项 is 都成立。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#引用相等

def 步骤键(回合,步):#回合与步骤合成索引键
    """turn:step。"""
    return str(回合)+':'+str(步)#键

def 位置坐标(位置):#从位置取出回合与步骤坐标
    """其它种类无坐标。"""
    种=取字段(位置,'kind')#种
    if 种=='step':#步骤
        return {'turn':取字段(取字段(位置,'turn'),'turn'),'step':取字段(取字段(位置,'step'),'step')}#双坐标
    if 种=='turn':#回合
        return {'turn':取字段(取字段(位置,'turn'),'turn')}#回合
    return {}#无

def 位置身份(位置):#位置的稳定身份字符串
    """kind:回合:步骤。"""
    坐标=位置坐标(位置)#坐标
    return str(取字段(位置,'kind'))+':'+str(坐标.get('turn') or '')+':'+str(坐标.get('step') or '')#身份

def 有序可见(节点们):#可见节点按锚点序号再按 key 排序
    """只要可见。"""
    可见=[节 for 节 in 节点们 if 取字段(节,'visibility')=='visible']#可见
    return sorted(可见,key=lambda 节:(取字段(节,'anchorSeq',0),取字段(节,'key') or ''))#排序

class 可变聊天节点仓:#可变的按 key 节点仓
    """get / values / replace / upsert。"""
    def __init__(自身):#空仓
        """key → 视图节点。"""
        自身.按键={}#表
        自身.值缓存=list(空列表)#values 缓存
        自身.值脏=False#缓存是否脱节

    def get(自身,键):#按 key 取节点
        """没有则为 None。"""
        return 自身.按键.get(键)#节点

    def values(自身):#全部节点；脏了才重建
        """只读值列表。"""
        if 自身.值脏:#脱节
            自身.值缓存=list(自身.按键.values())#重建
            自身.值脏=False#对齐
        return 自身.值缓存#列表

    def replace(自身,节点们):#全量换成这些节点
        """立刻重建值缓存。"""
        自身.按键.clear()#清空
        for 节 in 节点们:#放入
            自身.按键[取字段(节,'key')]=节#按 key
        自身.值缓存=list(自身.按键.values())#重建
        自身.值脏=False#对齐

    def upsert(自身,节点们):#按 key 写入；引用相同则跳过
        """有变化则脏值缓存。"""
        变了=False#是否换了
        for 节 in 节点们:#逐个
            键=取字段(节,'key')#key
            if 自身.按键.get(键) is 节:#同一引用
                continue#跳过
            自身.按键[键]=节#换
            变了=True#记下
        if 变了:#有变化
            自身.值脏=True#脏

class 可变聊天位置索引:#按回合/步骤聚合节点 key
    """getTurn / getStep / rebuild / touch。"""
    def __init__(自身):#空索引
        """回合/步骤表。"""
        自身.回合们={}#回合 → keys
        自身.步骤们={}#步骤键 → keys

    def getTurn(自身,回合):#该回合下的节点 key
        """缺席回空。"""
        return 自身.回合们.get(回合,空键)#列表

    def getStep(自身,回合,步):#该步骤下的节点 key
        """缺席回空。"""
        return 自身.步骤们.get(步骤键(回合,步),空键)#列表

    def rebuild(自身,序,仓):#按可见序重建回合/步骤索引
        """能沿用旧列表引用则沿用。"""
        回合表={}#可变
        步骤表={}#可变
        for 键 in 序:#按可见序
            节=仓.get(键)#节点
            位置=取字段(节,'location') if 节 is not None else None#位置
            if 位置 is None:#无
                continue#跳过
            坐标=位置坐标(位置)#坐标
            if 坐标.get('turn') is None:#无回合
                continue#跳过
            回合号=坐标['turn']#回合
            回合表.setdefault(回合号,[]).append(键)#追加
            if 坐标.get('step') is None:#无步骤
                continue#只进回合
            步键=步骤键(回合号,坐标['step'])#步骤键
            步骤表.setdefault(步键,[]).append(键)#追加
        自身.回合们=更新索引(自身.回合们,回合表)#稳定引用
        自身.步骤们=更新索引(自身.步骤们,步骤表)#同上

    def touch(自身,节点们):#复制受影响回合/步骤的 key 列表
        """成员数据变了但位置没动时换身份。"""
        回合集=set()#需换身份的回合
        步骤集=set()#需换身份的步骤
        for 节 in 节点们:#逐个
            坐标=位置坐标(取字段(节,'location'))#坐标
            回合号=坐标.get('turn')#回合
            if 回合号 is None:#无
                continue#跳过
            键们=自身.回合们.get(回合号)#该回合 keys
            if 键们 is None or 取字段(节,'key') not in 键们:#不在
                continue#跳过
            回合集.add(回合号)#记下
            if 坐标.get('step') is not None:#有步
                步骤集.add(步骤键(回合号,坐标['step']))#记下
        for 回合号 in 回合集:#换回合身份
            键们=自身.回合们.get(回合号)#现有
            if 键们 is not None:#有
                自身.回合们[回合号]=list(键们)#浅拷
        for 步键 in 步骤集:#换步骤身份
            键们=自身.步骤们.get(步键)#现有
            if 键们 is not None:#有
                自身.步骤们[步键]=list(键们)#浅拷

def 更新索引(先前,下一可变):#能沿用旧列表引用则沿用
    """避免无谓通知。"""
    下一={}#结果
    键集=set(先前.keys())|set(下一可变.keys())#并集
    for 键 in 键集:#逐键
        前=先前.get(键,空键)#旧
        候=下一可变.get(键,空键)#新
        值=前 if 同引用(前,候) else 候#沿用或换
        if len(候)>0:#非空才入表
            下一[键]=值#写入
    return 下一#稳定索引

空贡献={'anchorSeq':0,'nodes':空列表,'partial':None,'running':None}#空贡献

def 遗留贡献(原始):#视图节点投影成遗留贡献
    """按渲染器 kind 分发。"""
    种=取字段(原始,'kind')#kind
    可见=取字段(原始,'visibility')#可见性
    数据=取字段(原始,'data')#载荷
    锚=取字段(原始,'anchorSeq',0)#锚点
    if 可见!='visible' and 种!='assistant-step':#隐藏且非助手
        return 空贡献#不贡献
    if 种 in ('user','steering','context','command','compaction','turn-error','turn-max-tokens','unknown'):#单节点
        return {'anchorSeq':锚,'nodes':[数据],'partial':None,'running':None}#定稿流
    if 种=='assistant-step':#助手步骤
        if 取字段(数据,'status')=='running':#仍在流式
            if 可见!='visible':#隐藏运行中
                return 空贡献#不贡献
            return {'anchorSeq':锚,'nodes':空列表,'partial':{'turn':取字段(数据,'turn'),'step':取字段(数据,'step'),'blocks':取字段(数据,'blocks')},'running':None}#partial
        终=取字段(数据,'finalNode')#定稿
        return {'anchorSeq':锚,'nodes':空列表 if 终 is None else [终],'partial':None,'running':None}#已结算
    if 种=='tool-call':#工具
        根=取字段(数据,'root')#根
        if 运行中工具(根):#仍运行
            return {'anchorSeq':锚,'nodes':空列表,'partial':None,'running':根}#running
        return {'anchorSeq':锚,'nodes':[根],'partial':None,'running':None}#定稿
    if 种=='manual-compaction':#手动压缩
        命令=取字段(数据,'command')#命令
        压缩=取字段(数据,'compaction')#压缩
        节点们=[命令] if 压缩 is None else [命令,压缩]#列表
        return {'anchorSeq':锚,'nodes':节点们,'partial':None,'running':None}#贡献
    if 种=='model-retry':#重试
        return {'anchorSeq':锚,'nodes':取字段(数据,'attempts') or [],'partial':None,'running':None}#尝试们
    if 种=='turn-tail':#回合尾
        return 空贡献#不进兼容流
    return 空贡献#未识别

def 同贡献(左,右):#两条贡献是否同一身份
    """锚点/partial/running/nodes 引用。"""
    if 左 is None:#无左
        return False#不同
    左偏=左.get('partial')#左 partial
    右偏=右.get('partial')#右 partial
    return (左.get('anchorSeq')==右.get('anchorSeq')
        and (取字段(左偏,'blocks') if 左偏 else None)==(取字段(右偏,'blocks') if 右偏 else None)
        and (取字段(左偏,'turn') if 左偏 else None)==(取字段(右偏,'turn') if 右偏 else None)
        and (取字段(左偏,'step') if 左偏 else None)==(取字段(右偏,'step') if 右偏 else None)
        and 左.get('running') is 右.get('running')
        and 同引用(左.get('nodes') or [],右.get('nodes') or []))#全同

def 更新贡献索引(索引,键,贡献,在场):#按 present 写入或删出分表
    """在场则写入。"""
    if 在场:#应收录
        索引[键]=贡献#写入
    else:#否则
        索引.pop(键,None)#删除

def 定稿贡献变了(先前,下一):#定稿流是否要重建
    """节点列表或锚点变了。"""
    前节=先前.get('nodes') if 先前 else 空列表#旧
    前节=前节 or 空列表#缺省
    下节=下一.get('nodes') or 空列表#新
    if not 同引用(前节,下节):#列表不同
        return True#变
    if (len(前节)>0 or len(下节)>0) and (先前 or {}).get('anchorSeq')!=下一.get('anchorSeq'):#锚点变
        return True#变
    return False#不变

def 运行贡献变了(先前,下一):#运行中列表是否要重建
    """running 引用或锚点变了。"""
    前跑=(先前 or {}).get('running')#旧
    下跑=下一.get('running')#新
    if 前跑 is not 下跑:#引用不同
        return True#变
    if (前跑 is not None or 下跑 is not None) and (先前 or {}).get('anchorSeq')!=下一.get('anchorSeq'):#锚点变
        return True#变
    return False#不变

def 局部贡献变了(先前,下一):#局部助手是否要重建
    """partial 字段或锚点变了。"""
    左偏=(先前 or {}).get('partial')#旧
    右偏=下一.get('partial')#新
    if 取字段(左偏,'blocks')!=取字段(右偏,'blocks'):#块不同
        return True#变
    if 取字段(左偏,'turn')!=取字段(右偏,'turn') or 取字段(左偏,'step')!=取字段(右偏,'step'):#坐标不同
        return True#变
    if ((左偏 is not None or 右偏 is not None) and (先前 or {}).get('anchorSeq')!=下一.get('anchorSeq')):#锚点变
        return True#变
    return False#不变

class 遗留切片构建器:#遗留切片的增量投影
    """replace / apply。"""
    def __init__(自身):#空
        """分表与缓存。"""
        自身.贡献们={}#总表
        自身.定稿贡献={}#定稿分表
        自身.运行贡献={}#运行分表
        自身.局部贡献={}#局部分表
        自身.定稿=list(空列表)#定稿流
        自身.运行调用=list(空列表)#运行中工具
        自身.局部=None#局部助手
        自身.时间线=None#上次时间线
        自身.回合计时={}#计时
        自身.回合结束={}#结束序号

    def 索引贡献(自身,键,贡献):#按贡献内容写入三个分表
        """有内容才进对应分表。"""
        更新贡献索引(自身.定稿贡献,键,贡献,len(贡献.get('nodes') or [])>0)#定稿
        更新贡献索引(自身.运行贡献,键,贡献,贡献.get('running') is not None)#运行
        更新贡献索引(自身.局部贡献,键,贡献,贡献.get('partial') is not None)#局部

    def 重建定稿(自身):#按序号重排定稿节点列表
        """引用变了才换。"""
        摊=[]#摊平
        for 值 in 自身.定稿贡献.values():#贡献
            摊.extend(值.get('nodes') or [])#节点
        定稿=sorted(摊,key=lambda 节:取字段(节,'seq',0))#按 seq
        if not 同引用(自身.定稿,定稿):#变了
            自身.定稿=定稿#换

    def 重建运行(自身):#按锚点重排运行中工具
        """引用变了才换。"""
        排=sorted(自身.运行贡献.values(),key=lambda 值:值.get('anchorSeq',0))#锚点升序
        运行=[值['running'] for 值 in 排 if 值.get('running') is not None]#抽出
        if not 同引用(自身.运行调用,运行):#变了
            自身.运行调用=运行#换

    def 重建局部(自身):#取锚点最大的那条局部助手
        """块/坐标变了才换。"""
        排=sorted(自身.局部贡献.values(),key=lambda 值:值.get('anchorSeq',0))#升序
        局部=None#结果
        for 值 in 排:#找最后非空
            if 值.get('partial') is not None:#有
                局部=值['partial']#记下
        旧=自身.局部#旧
        if 取字段(旧,'blocks')!=取字段(局部,'blocks') or 取字段(旧,'turn')!=取字段(局部,'turn') or 取字段(旧,'step')!=取字段(局部,'step'):#不同
            自身.局部=局部#换

    def 更新时间线(自身,时间线):#时间线身份变了才重投影计时
        """同一引用则跳过。"""
        if 自身.时间线 is 时间线:#同一
            return#跳过
        自身.时间线=时间线#记下
        计时={}#回合 → 起止
        结束={}#回合 → 结束序号
        回合们=取字段(时间线,'turns')#turns
        值们=回合们.values() if hasattr(回合们,'values') else (回合们 or [])#可迭代
        for 回合 in 值们:#遍历
            开始=取字段(回合,'start')#开始
            if 开始 is not None:#有开始
                项={'startTime':取字段(开始,'time')}#起
                终=取字段(回合,'end')#结束
                if 终 is not None:#有结束
                    项['endTime']=取字段(终,'time')#带 endTime
                计时[取字段(回合,'turn')]=项#写入
            终=取字段(回合,'end')#结束
            if 终 is not None:#有
                结束[取字段(回合,'turn')]=取字段(终,'seq')#结束序号
        自身.回合计时=计时#换
        自身.回合结束=结束#换

    def 快照(自身):#读出当前兼容切片
        """切片字段。"""
        return {'nodes':自身.定稿,'turnTimings':自身.回合计时,'turnEnds':自身.回合结束,'partial':自身.局部,'runningCalls':自身.运行调用}#切片

    def replace(自身,节点们,时间线):#全量重算兼容切片
        """清空分表后投影。"""
        自身.贡献们.clear()#清空
        自身.定稿贡献.clear()#清空
        自身.运行贡献.clear()#清空
        自身.局部贡献.clear()#清空
        for 节 in 节点们:#逐节点
            贡献=遗留贡献(节)#投影
            键=取字段(节,'key')#key
            自身.贡献们[键]=贡献#总表
            自身.索引贡献(键,贡献)#分表
        自身.重建定稿()#重排
        自身.重建运行()#重排
        自身.重建局部()#重选
        自身.更新时间线(时间线)#计时
        return 自身.快照()#读出

    def apply(自身,写入们,时间线):#增量更新兼容切片
        """身份相同则跳过。"""
        定稿变=False#定稿是否重建
        运行变=False#运行是否重建
        局部变=False#局部是否重建
        for 节 in 写入们:#逐条
            贡献=遗留贡献(节)#新贡献
            键=取字段(节,'key')#key
            先前=自身.贡献们.get(键)#旧
            if 同贡献(先前,贡献):#相同
                continue#跳过
            定稿变=定稿变 or 定稿贡献变了(先前,贡献)#定稿
            运行变=运行变 or 运行贡献变了(先前,贡献)#运行
            局部变=局部变 or 局部贡献变了(先前,贡献)#局部
            自身.贡献们[键]=贡献#总表
            自身.索引贡献(键,贡献)#分表
        if 定稿变:#定稿变了
            自身.重建定稿()#重排
        if 运行变:#运行变了
            自身.重建运行()#重排
        if 局部变:#局部变了
            自身.重建局部()#重选
        自身.更新时间线(时间线)#计时
        return 自身.快照()#读出

class 聊天快照构建器:#增量 Chat 快照构建器
    """replace / apply；登记在 chat 目标下。"""
    def __init__(自身):#造空快照
        """仓、索引、遗留。"""
        自身.仓=可变聊天节点仓()#按 key
        自身.位置=可变聊天位置索引()#位置索引
        自身.遗留=遗留切片构建器()#遗留
        自身.序=list(空键)#可见 key 序
        自身.empty=自身.组装({'turnOrder':空回合,'turns':{}},自身.遗留.replace(空列表,{'turnOrder':空回合,'turns':{}}))#空快照

    def replace(自身,输入):#全量替换节点与时间线
        """仓全量 + 重建索引。"""
        节点们=取字段(输入,'nodes') or []#节点
        时间线=取字段(输入,'timeline')#时间线
        自身.仓.replace(节点们)#全量
        自身.序=[取字段(节,'key') for 节 in 有序可见(节点们)]#可见序
        自身.位置.rebuild(自身.序,自身.仓)#重建索引
        return 自身.组装(时间线,自身.遗留.replace(节点们,时间线))#快照

    def apply(自身,输入):#增量 upsert 节点与时间线
        """结构变化则重排；仅内容变则 touch。"""
        写入=取字段(输入,'upserts') or []#写入
        时间线=取字段(输入,'timeline')#时间线
        结构=False#是否结构变
        仅内容=[]#仅内容变
        for 节 in 写入:#逐条
            先前=自身.仓.get(取字段(节,'key'))#已有
            本结构=(先前 is None
                or 取字段(先前,'anchorSeq')!=取字段(节,'anchorSeq')
                or 取字段(先前,'visibility')!=取字段(节,'visibility')
                or 位置身份(取字段(先前,'location'))!=位置身份(取字段(节,'location')))#结构判定
            结构=结构 or 本结构#整次
            if not 本结构:#仅内容
                仅内容.append(节)#记下
        自身.仓.upsert(写入)#写入仓
        if 结构:#结构变
            下一=[取字段(节,'key') for 节 in 有序可见(自身.仓.values())]#新序
            自身.序=自身.序 if 同引用(自身.序,下一) else 下一#沿用或换
            自身.位置.rebuild(自身.序,自身.仓)#重建
        自身.位置.touch(仅内容)#触达
        return 自身.组装(时间线,自身.遗留.apply(写入,时间线))#快照

    def 组装(自身,时间线,遗留=None):#组装 ChatSnapshot
        """快照字段。"""
        if 遗留 is None:#缺省
            遗留=自身.遗留.replace(空列表,时间线)#空节点全量
        return {'order':自身.序,'nodes':自身.仓,'locations':自身.位置,'timeline':时间线,'legacy':遗留}#快照

聊天视图定义={#Chat 目标定义
    'target':'chat',#目标名
    'create':lambda:聊天快照构建器(),#每次新建
}#结束

def 登记聊天会话视图(上下文):#把定义挂到视图注册表
    """conversationViews.register。"""
    上下文.conversationViews.register(聊天视图定义)#登记

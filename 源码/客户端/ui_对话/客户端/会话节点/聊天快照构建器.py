from ..约定.聊天节点 import 运行中工具#运行中判断

__all__=['聊天快照构建器','聊天视图定义','登记聊天会话视图']#仅中文公开名

空键=()#空 key 列表
空回合=()#空回合号
空列表=()#空只读列表

def 同引用(左,右):
    """长度与每项 is 都成立。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#引用相等

def 步骤键(回合,步):
    """turn:step。"""
    return str(回合)+':'+str(步)#键

def 位置坐标(位置):
    """其它种类无坐标。位置为 dict。"""
    if 位置 is None:#无
        return {}#无
    种=位置['kind'] if 'kind' in 位置 else None#种
    if 种=='step':#步骤
        回合位=位置['turn'] if 'turn' in 位置 else None#回合位
        步位=位置['step'] if 'step' in 位置 else None#步位
        return {#双坐标
            'turn':回合位['turn'] if 回合位 is not None and 'turn' in 回合位 else None,#回合
            'step':步位['step'] if 步位 is not None and 'step' in 步位 else None,#步骤
        }#结束
    if 种=='turn':#回合
        回合位=位置['turn'] if 'turn' in 位置 else None#回合位
        return {'turn':回合位['turn'] if 回合位 is not None and 'turn' in 回合位 else None}#回合
    return {}#无

def 位置身份(位置):
    """kind:回合:步骤。"""
    坐标=位置坐标(位置)#坐标
    种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
    回合串=str(坐标['turn']) if 'turn' in 坐标 and 坐标['turn'] is not None else ''#回合
    步串=str(坐标['step']) if 'step' in 坐标 and 坐标['step'] is not None else ''#步骤
    return str(种)+':'+回合串+':'+步串#身份

def 可见排序键(节):
    """锚点序号再按 key。"""
    锚=节['anchorSeq'] if 'anchorSeq' in 节 else 0#锚
    键=节['key'] if 'key' in 节 and 节['key'] is not None else ''#key
    return (锚,键)#排序键

def 有序可见(节点列表):
    """只要可见。"""
    可见=[节 for 节 in 节点列表 if 'visibility' in 节 and 节['visibility']=='visible']#可见
    return sorted(可见,key=可见排序键)#排序

def 序号键(节):
    """定稿节点 seq。"""
    return 节['seq'] if 'seq' in 节 else 0#序号

def 锚点键(值):
    """贡献锚点。"""
    return 值['anchorSeq'] if 'anchorSeq' in 值 else 0#锚点

def 贡献锚(贡献):
    """贡献的 anchorSeq；缺席为 None。"""
    if 贡献 is None or 'anchorSeq' not in 贡献:#无
        return None#缺
    return 贡献['anchorSeq']#锚

def 取贡献节点列表(贡献):
    """贡献 nodes；缺席或空容器保持空列表。"""
    if 贡献 is None or 'nodes' not in 贡献 or 贡献['nodes'] is None:#无
        return 空列表#空
    return 贡献['nodes']#节点

class 可变聊天节点存储:
    """get / values / replace / upsert。快照存储公开面保持这些方法名。"""
    def __init__(自身):
        """key → 视图节点。"""
        自身.按键={}#表
        自身.值缓存=list(空列表)#values 缓存
        自身.值脏=False#缓存是否脱节

    def get(自身,键):
        """没有则为 None。"""
        return 自身.按键[键] if 键 in 自身.按键 else None#节点

    def values(自身):
        """只读值列表。"""
        if 自身.值脏:#脱节
            自身.值缓存=list(自身.按键.values())#重建
            自身.值脏=False#对齐
        return 自身.值缓存#列表

    def replace(自身,节点列表):
        """立刻重建值缓存。"""
        自身.按键.clear()#清空
        for 节 in 节点列表:#放入
            自身.按键[节['key']]=节#按 key
        自身.值缓存=list(自身.按键.values())#重建
        自身.值脏=False#对齐

    def upsert(自身,节点列表):
        """有变化则脏值缓存。"""
        变了=False#是否换了
        for 节 in 节点列表:#逐个
            键=节['key']#key
            if 键 in 自身.按键 and 自身.按键[键] is 节:#同一引用
                continue#跳过
            自身.按键[键]=节#换
            变了=True#记下
        if 变了:#有变化
            自身.值脏=True#脏

class 可变聊天位置索引:
    """getTurn / getStep / rebuild / touch。快照位置索引公开面。"""
    def __init__(自身):
        """回合/步骤表。"""
        自身.回合表={}#回合 → keys
        自身.步骤表={}#步骤键 → keys

    def getTurn(自身,回合):
        """缺席回空。"""
        return 自身.回合表[回合] if 回合 in 自身.回合表 else 空键#列表

    def getStep(自身,回合,步):
        """缺席回空。"""
        键=步骤键(回合,步)#步骤键
        return 自身.步骤表[键] if 键 in 自身.步骤表 else 空键#列表

    def rebuild(自身,序,节点存储):
        """能沿用旧列表引用则沿用。"""
        回合表={}#可变
        步骤表={}#可变
        for 键 in 序:#按可见序
            节=节点存储.get(键)#节点
            位置=节['location'] if 节 is not None and 'location' in 节 else None#位置
            if 位置 is None:#无
                continue#跳过
            坐标=位置坐标(位置)#坐标
            if 'turn' not in 坐标 or 坐标['turn'] is None:#无回合
                continue#跳过
            回合号=坐标['turn']#回合
            if 回合号 not in 回合表:#新回合
                回合表[回合号]=[]#开
            回合表[回合号].append(键)#追加
            if 'step' not in 坐标 or 坐标['step'] is None:#无步骤
                continue#只进回合
            步键=步骤键(回合号,坐标['step'])#步骤键
            if 步键 not in 步骤表:#新步骤
                步骤表[步键]=[]#开
            步骤表[步键].append(键)#追加
        自身.回合表=更新索引(自身.回合表,回合表)#稳定引用
        自身.步骤表=更新索引(自身.步骤表,步骤表)#同上

    def touch(自身,节点列表):
        """成员数据变了但位置没动时换身份。"""
        回合集=set()#需换身份的回合
        步骤集=set()#需换身份的步骤
        for 节 in 节点列表:#逐个
            坐标=位置坐标(节['location'] if 'location' in 节 else None)#坐标
            if 'turn' not in 坐标 or 坐标['turn'] is None:#无
                continue#跳过
            回合号=坐标['turn']#回合
            键列表=自身.回合表[回合号] if 回合号 in 自身.回合表 else None#该回合 keys
            节键=节['key'] if 'key' in 节 else None#key
            if 键列表 is None or 节键 not in 键列表:#不在
                continue#跳过
            回合集.add(回合号)#记下
            if 'step' in 坐标 and 坐标['step'] is not None:#有步
                步骤集.add(步骤键(回合号,坐标['step']))#记下
        for 回合号 in 回合集:#换回合身份
            键列表=自身.回合表[回合号] if 回合号 in 自身.回合表 else None#现有
            if 键列表 is not None:#有
                自身.回合表[回合号]=list(键列表)#浅拷
        for 步键 in 步骤集:#换步骤身份
            键列表=自身.步骤表[步键] if 步键 in 自身.步骤表 else None#现有
            if 键列表 is not None:#有
                自身.步骤表[步键]=list(键列表)#浅拷

def 更新索引(先前,下一可变):
    """避免无谓通知。"""
    下一={}#结果
    键集=set(先前.keys())|set(下一可变.keys())#并集
    for 键 in 键集:#逐键
        前=先前[键] if 键 in 先前 else 空键#旧
        候=下一可变[键] if 键 in 下一可变 else 空键#新
        值=前 if 同引用(前,候) else 候#沿用或换
        if len(候)>0:#非空才入表
            下一[键]=值#写入
    return 下一#稳定索引

空贡献={'anchorSeq':0,'nodes':空列表,'partial':None,'running':None}#空贡献

def 遗留贡献(原始):
    """按渲染器 kind 分发。原始为视图节点 dict。"""
    种=原始['kind'] if 'kind' in 原始 else None#kind
    可见=原始['visibility'] if 'visibility' in 原始 else None#可见性
    数据=原始['data'] if 'data' in 原始 else None#载荷
    锚=原始['anchorSeq'] if 'anchorSeq' in 原始 else 0#锚点
    if 可见!='visible' and 种!='assistant-step':#隐藏且非助手
        return 空贡献#不贡献
    if 种 in ('user','steering','context','command','compaction','turn-error','turn-max-tokens','unknown'):#单节点
        return {'anchorSeq':锚,'nodes':[数据],'partial':None,'running':None}#定稿流
    if 种=='assistant-step':#助手步骤
        状态=数据['status'] if 数据 is not None and 'status' in 数据 else None#状态
        if 状态=='running':#仍在流式
            if 可见!='visible':#隐藏运行中
                return 空贡献#不贡献
            return {#partial
                'anchorSeq':锚,'nodes':空列表,#无定稿
                'partial':{#局部
                    'turn':数据['turn'] if 'turn' in 数据 else None,#回合
                    'step':数据['step'] if 'step' in 数据 else None,#步骤
                    'blocks':数据['blocks'] if 'blocks' in 数据 else None,#块
                },#局部结束
                'running':None,#无运行工具
            }#结束
        终=数据['finalNode'] if 数据 is not None and 'finalNode' in 数据 else None#定稿
        return {'anchorSeq':锚,'nodes':空列表 if 终 is None else [终],'partial':None,'running':None}#已结算
    if 种=='tool-call':#工具
        根=数据['root'] if 数据 is not None and 'root' in 数据 else None#根
        if 运行中工具(根):#仍运行
            return {'anchorSeq':锚,'nodes':空列表,'partial':None,'running':根}#running
        return {'anchorSeq':锚,'nodes':[根],'partial':None,'running':None}#定稿
    if 种=='manual-compaction':#手动压缩
        命令=数据['command'] if 数据 is not None and 'command' in 数据 else None#命令
        压缩=数据['compaction'] if 数据 is not None and 'compaction' in 数据 else None#压缩
        节点列表=[命令] if 压缩 is None else [命令,压缩]#列表
        return {'anchorSeq':锚,'nodes':节点列表,'partial':None,'running':None}#贡献
    if 种=='model-retry':#重试
        尝试=数据['attempts'] if 数据 is not None and 'attempts' in 数据 and 数据['attempts'] is not None else []#尝试列表
        return {'anchorSeq':锚,'nodes':尝试,'partial':None,'running':None}#尝试列表
    if 种=='turn-tail':#回合尾
        return 空贡献#不进兼容流
    return 空贡献#未识别

def 偏字段(偏,键):
    """partial 上的字段；偏为 None 则 None。"""
    if 偏 is None or 键 not in 偏:#无
        return None#缺
    return 偏[键]#值

def 同贡献(左,右):
    """锚点/partial/running/nodes 引用。"""
    if 左 is None:#无左
        return False#不同
    左偏=左['partial'] if 'partial' in 左 else None#左 partial
    右偏=右['partial'] if 'partial' in 右 else None#右 partial
    左跑=左['running'] if 'running' in 左 else None#左 running
    右跑=右['running'] if 'running' in 右 else None#右 running
    左节=取贡献节点列表(左)#左节点
    右节=取贡献节点列表(右)#右节点
    return (贡献锚(左)==贡献锚(右)
        and 偏字段(左偏,'blocks')==偏字段(右偏,'blocks')
        and 偏字段(左偏,'turn')==偏字段(右偏,'turn')
        and 偏字段(左偏,'step')==偏字段(右偏,'step')
        and 左跑 is 右跑
        and 同引用(左节,右节))#全同

def 更新贡献索引(索引,键,贡献,在场):
    """在场则写入。"""
    if 在场:#应收录
        索引[键]=贡献#写入
    else:#否则
        if 键 in 索引:#有
            del 索引[键]#删除

def 定稿贡献变了(先前,下一):
    """节点列表或锚点变了。"""
    前节=取贡献节点列表(先前)#旧
    下节=取贡献节点列表(下一)#新
    if not 同引用(前节,下节):#列表不同
        return True#变
    if (len(前节)>0 or len(下节)>0) and 贡献锚(先前)!=贡献锚(下一):#锚点变
        return True#变
    return False#不变

def 运行贡献变了(先前,下一):
    """running 引用或锚点变了。"""
    前跑=先前['running'] if 先前 is not None and 'running' in 先前 else None#旧
    下跑=下一['running'] if 'running' in 下一 else None#新
    if 前跑 is not 下跑:#引用不同
        return True#变
    if (前跑 is not None or 下跑 is not None) and 贡献锚(先前)!=贡献锚(下一):#锚点变
        return True#变
    return False#不变

def 局部贡献变了(先前,下一):
    """partial 字段或锚点变了。"""
    左偏=先前['partial'] if 先前 is not None and 'partial' in 先前 else None#旧
    右偏=下一['partial'] if 'partial' in 下一 else None#新
    if 偏字段(左偏,'blocks')!=偏字段(右偏,'blocks'):#块不同
        return True#变
    if 偏字段(左偏,'turn')!=偏字段(右偏,'turn') or 偏字段(左偏,'step')!=偏字段(右偏,'step'):#坐标不同
        return True#变
    if (左偏 is not None or 右偏 is not None) and 贡献锚(先前)!=贡献锚(下一):#锚点变
        return True#变
    return False#不变

class 遗留切片构建器:
    """replace / apply。遗留切片公开面。"""
    def __init__(自身):
        """分表与缓存。"""
        自身.贡献表={}#总表
        自身.定稿贡献={}#定稿分表
        自身.运行贡献={}#运行分表
        自身.局部贡献={}#局部分表
        自身.定稿=list(空列表)#定稿流
        自身.运行调用=list(空列表)#运行中工具
        自身.局部=None#局部助手
        自身.时间线=None#上次时间线
        自身.回合计时={}#计时
        自身.回合结束={}#结束序号

    def 索引贡献(自身,键,贡献):
        """有内容才进对应分表。"""
        更新贡献索引(自身.定稿贡献,键,贡献,len(取贡献节点列表(贡献))>0)#定稿
        更新贡献索引(自身.运行贡献,键,贡献,('running' in 贡献 and 贡献['running'] is not None))#运行
        更新贡献索引(自身.局部贡献,键,贡献,('partial' in 贡献 and 贡献['partial'] is not None))#局部

    def 重建定稿(自身):
        """引用变了才换。"""
        摊=[]#摊平
        for 值 in 自身.定稿贡献.values():#贡献
            摊.extend(取贡献节点列表(值))#节点
        定稿=sorted(摊,key=序号键)#按 seq
        if not 同引用(自身.定稿,定稿):#变了
            自身.定稿=定稿#换

    def 重建运行(自身):
        """引用变了才换。"""
        排=sorted(自身.运行贡献.values(),key=锚点键)#锚点升序
        运行=[]#抽出
        for 值 in 排:#扫
            if 'running' in 值 and 值['running'] is not None:#有
                运行.append(值['running'])#收下
        if not 同引用(自身.运行调用,运行):#变了
            自身.运行调用=运行#换

    def 重建局部(自身):
        """块/坐标变了才换。"""
        排=sorted(自身.局部贡献.values(),key=锚点键)#升序
        局部=None#结果
        for 值 in 排:#找最后非空
            if 'partial' in 值 and 值['partial'] is not None:#有
                局部=值['partial']#记下
        旧=自身.局部#旧
        if 偏字段(旧,'blocks')!=偏字段(局部,'blocks') or 偏字段(旧,'turn')!=偏字段(局部,'turn') or 偏字段(旧,'step')!=偏字段(局部,'step'):#不同
            自身.局部=局部#换

    def 更新时间线(自身,时间线):
        """同一引用则跳过。时间线为 dict。"""
        if 自身.时间线 is 时间线:#同一
            return#跳过
        自身.时间线=时间线#记下
        计时={}#回合 → 起止
        结束={}#回合 → 结束序号
        回合表=时间线['turns'] if 时间线 is not None and 'turns' in 时间线 and 时间线['turns'] is not None else {}#turns
        for 回合 in 回合表.values():#遍历
            开始=回合['start'] if 'start' in 回合 else None#开始
            回合号=回合['turn'] if 'turn' in 回合 else None#回合号
            if 开始 is not None:#有开始
                项={'startTime':开始['time'] if 'time' in 开始 else None}#起
                终=回合['end'] if 'end' in 回合 else None#结束
                if 终 is not None:#有结束
                    项['endTime']=终['time'] if 'time' in 终 else None#带 endTime
                计时[回合号]=项#写入
            终=回合['end'] if 'end' in 回合 else None#结束
            if 终 is not None:#有
                结束[回合号]=终['seq'] if 'seq' in 终 else None#结束序号
        自身.回合计时=计时#换
        自身.回合结束=结束#换

    def 快照(自身):
        """切片字段。"""
        return {'nodes':自身.定稿,'turnTimings':自身.回合计时,'turnEnds':自身.回合结束,'partial':自身.局部,'runningCalls':自身.运行调用}#切片

    def replace(自身,节点列表,时间线):
        """全量重算兼容切片。"""
        自身.贡献表.clear()#清空
        自身.定稿贡献.clear()#清空
        自身.运行贡献.clear()#清空
        自身.局部贡献.clear()#清空
        for 节 in 节点列表:#逐节点
            贡献=遗留贡献(节)#投影
            键=节['key']#key
            自身.贡献表[键]=贡献#总表
            自身.索引贡献(键,贡献)#分表
        自身.重建定稿()#重排
        自身.重建运行()#重排
        自身.重建局部()#重选
        自身.更新时间线(时间线)#计时
        return 自身.快照()#读出

    def apply(自身,写入列表,时间线):
        """身份相同则跳过。"""
        定稿变=False#定稿是否重建
        运行变=False#运行是否重建
        局部变=False#局部是否重建
        for 节 in 写入列表:#逐条
            贡献=遗留贡献(节)#新贡献
            键=节['key']#key
            先前=自身.贡献表[键] if 键 in 自身.贡献表 else None#旧
            if 同贡献(先前,贡献):#相同
                continue#跳过
            定稿变=定稿变 or 定稿贡献变了(先前,贡献)#定稿
            运行变=运行变 or 运行贡献变了(先前,贡献)#运行
            局部变=局部变 or 局部贡献变了(先前,贡献)#局部
            自身.贡献表[键]=贡献#总表
            自身.索引贡献(键,贡献)#分表
        if 定稿变:#定稿变了
            自身.重建定稿()#重排
        if 运行变:#运行变了
            自身.重建运行()#重排
        if 局部变:#局部变了
            自身.重建局部()#重选
        自身.更新时间线(时间线)#计时
        return 自身.快照()#读出

class 聊天快照构建器:
    """replace / apply；登记在 chat 目标下。"""
    def __init__(自身):
        """存储、索引、遗留。"""
        自身.节点存储=可变聊天节点存储()#按 key
        自身.位置=可变聊天位置索引()#位置索引
        自身.遗留=遗留切片构建器()#遗留
        自身.序=list(空键)#可见 key 序
        空时间线={'turnOrder':空回合,'turns':{}}#空时间线
        自身.empty=自身.组装(空时间线,自身.遗留.replace(空列表,空时间线))#空快照

    def replace(自身,输入):
        """存储全量 + 重建索引。输入为 dict。"""
        节点列表=输入['nodes'] if 'nodes' in 输入 and 输入['nodes'] is not None else []#节点
        时间线=输入['timeline'] if 'timeline' in 输入 else None#时间线
        自身.节点存储.replace(节点列表)#全量
        自身.序=[节['key'] for 节 in 有序可见(节点列表)]#可见序
        自身.位置.rebuild(自身.序,自身.节点存储)#重建索引
        return 自身.组装(时间线,自身.遗留.replace(节点列表,时间线))#快照

    def apply(自身,输入):
        """结构变化则重排；仅内容变则 touch。输入为 dict。"""
        写入=输入['upserts'] if 'upserts' in 输入 and 输入['upserts'] is not None else []#写入
        时间线=输入['timeline'] if 'timeline' in 输入 else None#时间线
        结构=False#是否结构变
        仅内容=[]#仅内容变
        for 节 in 写入:#逐条
            键=节['key']#key
            先前=自身.节点存储.get(键)#已有
            本结构=(先前 is None
                or (先前['anchorSeq'] if 'anchorSeq' in 先前 else None)!=(节['anchorSeq'] if 'anchorSeq' in 节 else None)
                or (先前['visibility'] if 'visibility' in 先前 else None)!=(节['visibility'] if 'visibility' in 节 else None)
                or 位置身份(先前['location'] if 'location' in 先前 else None)!=位置身份(节['location'] if 'location' in 节 else None))#结构判定
            结构=结构 or 本结构#整次
            if 本结构 is False:#仅内容
                仅内容.append(节)#记下
        自身.节点存储.upsert(写入)#写入存储
        if 结构:#结构变
            下一=[节['key'] for 节 in 有序可见(自身.节点存储.values())]#新序
            自身.序=自身.序 if 同引用(自身.序,下一) else 下一#沿用或换
            自身.位置.rebuild(自身.序,自身.节点存储)#重建
        自身.位置.touch(仅内容)#触达
        return 自身.组装(时间线,自身.遗留.apply(写入,时间线))#快照

    def 组装(自身,时间线,遗留=None):
        """快照字段。"""
        if 遗留 is None:#缺省
            遗留=自身.遗留.replace(空列表,时间线)#空节点全量
        return {'order':自身.序,'nodes':自身.节点存储,'locations':自身.位置,'timeline':时间线,'legacy':遗留}#快照

def 造聊天快照构建器():
    """每次新建构建器。"""
    return 聊天快照构建器()#新建

聊天视图定义={#Chat 目标定义
    'target':'chat',#目标名
    'create':造聊天快照构建器,#每次新建
}#结束

def 登记聊天会话视图(上下文):
    """conversationViews.register。"""
    上下文.conversationViews.register(聊天视图定义)#登记

"""无依赖源码引导闭包用的无损 JSON 快照与扁平线格式。"""
import math#有限数判定
from .协议 import 节点ptc错误#本包异常

__all__=['快照ptcjson值','编码ptcjson线','解码ptcjson线']#仅中文公开名

原生列表=list#模块捕获的 list
原生字典=dict#模块捕获的 dict
原生类型=type#模块捕获的 type
原生集合=set#模块捕获的 set
原生长度=len#模块捕获的 len

def 有朴素数组原型(值):#是否内建 list
    """是否内建 list，而不是子类。"""
    return 原生类型(值) is 原生列表#只要 list

def 有朴素对象原型(值):#是否内建 dict
    """是否内建 dict。"""
    return 原生类型(值) is 原生字典#只要 dict

def 可枚举字符串键(值):#JSON 可见键
    """返回每个 JSON 可见对象键；有 JSON 会丢掉的自有数据则拒绝。"""
    键列表=原生列表(值.keys())#自有键
    for 键 in 键列表:#逐键
        if 原生类型(键) is not str:#非字符串键
            return None#拒绝
    return 键列表#字符串键

def 是稠密数组(值):#是否恰好稠密下标加 length
    """数组是否稠密、无额外自有装饰。"""
    if not 有朴素数组原型(值):#非子类
        return False#否
    return True#Python list 稠密

def 键含有(键列表,期望):#精确键表是否含某键
    """不咨询原型地查找一个键。"""
    for 键 in 键列表:#逐键
        if 键==期望:#命中
            return True#含有
    return False#不含

def 快照ptcjson值(值):#校验并分离进程边界值
    """校验并分离一个进程边界值，不加载另一工作区包。镜像会话拥有的规范 JSON 边界。迭代遍历不加调用栈深度限制。值是候选完成值。返回分离的无损 JSON 快照；非法时为空。"""
    活动=原生集合()#环检测用 id
    根=[None]#分离根
    def 写入(目的,项):#写入目的槽
        """把项写入目的槽。"""
        if 目的['kind']=='root':#根
            根[0]=项#写根
        elif 目的['kind']=='array':#数组
            目的['target'][目的['index']]=项#写下标
        else:#对象
            目的['target'][目的['key']]=项#写键
    任务=[{'kind':'visit','value':值,'destination':{'kind':'root'}}]#根访问
    while 原生长度(任务)>0:#直到栈空
        当前=任务.pop()#弹出
        if 当前['kind']=='leave':#离开
            活动.discard(id(当前['source']))#出环集
            continue#下一
        if 当前['kind']=='array-item':#数组项
            下标=当前['index']#下标
            if 下标<0 or 下标>=原生长度(当前['source']):#越界即稀疏
                return None#拒绝
            任务.append({'kind':'visit','value':当前['source'][下标],'destination':{'kind':'array','target':当前['target'],'index':下标}})#访问
            continue#下一
        if 当前['kind']=='object-property':#对象属性
            任务.append({'kind':'visit','value':当前['source'][当前['key']],'destination':{'kind':'object','target':当前['target'],'key':当前['key']}})#访问
            continue#下一
        候选=当前['value']#访问值
        if 候选 is None:#null
            写入(当前['destination'],None)#写 null
            continue#下一
        if 原生类型(候选) is bool or 原生类型(候选) is str:#布尔或字符串
            写入(当前['destination'],候选)#原样
            continue#下一
        if 原生类型(候选) in (int,float) and 原生类型(候选) is not bool:#数字
            if not math.isfinite(候选):#非有限
                return None#拒绝
            if 候选==0.0 and math.copysign(1.0,候选)<0:#负零
                return None#拒绝
            写入(当前['destination'],候选)#写下
            continue#下一
        if 原生类型(候选) not in (原生列表,原生字典):#其它类型
            return None#拒绝
        标识=id(候选)#对象身份
        if 标识 in 活动:#环
            return None#拒绝
        if 原生类型(候选) is 原生列表:#数组
            if not 有朴素数组原型(候选):#非朴素
                return None#拒绝
            目标=[]#分离数组
            长度=原生长度(候选)#长度
            while 原生长度(目标)<长度:#预开槽
                目标.append(None)#占位
            写入(当前['destination'],目标)#写下
            活动.add(标识)#入环集
            任务.append({'kind':'leave','source':候选})#稍后离开
            下标=长度-1#逆序
            while 下标>=0:#逐项
                任务.append({'kind':'array-item','source':候选,'index':下标,'target':目标})#项
                下标-=1#推进
            continue#下一
        if not 有朴素对象原型(候选):#非朴素对象
            return None#拒绝
        键列表=可枚举字符串键(候选)#可见键
        if 键列表 is None:#非法键
            return None#拒绝
        目标={}#分离对象
        写入(当前['destination'],目标)#写下
        活动.add(标识)#入环集
        任务.append({'kind':'leave','source':候选})#稍后离开
        下标=原生长度(键列表)-1#逆序
        while 下标>=0:#逐键
            任务.append({'kind':'object-property','source':候选,'key':键列表[下标],'target':目标})#属性
            下标-=1#推进
    return 根[0]#分离根

def 编码ptcjson线(值):#把已校验 JSON 压成扁平线
    """把一个已校验 JSON 值压成进程控制通道用的前序记号流。值是无损 JSON。返回自身嵌套有界的前序记号流。"""
    线=[]#记号
    待办=[值]#待编码
    while 原生长度(待办)>0:#直到空
        当前=待办.pop()#弹出
        if 当前 is None or 原生类型(当前) in (bool,int,float,str):#标量
            线.append(当前)#写下
            continue#下一
        if 原生类型(当前) is 原生列表:#数组
            线.append({'kind':'array','length':原生长度(当前)})#数组标记
            下标=原生长度(当前)-1#逆序
            while 下标>=0:#逐项
                待办.append(当前[下标])#压栈
                下标-=1#推进
            continue#下一
        键列表=原生列表(当前.keys())#对象键
        线.append({'kind':'object','keys':键列表})#对象标记
        下标=原生长度(键列表)-1#逆序
        while 下标>=0:#逐键
            键=键列表[下标]#键
            待办.append(当前[键])#压属性
            下标-=1#推进
    return 线#扁平线

def 容器标记(值):#精确容器标记
    """返回一个精确容器标记；多/缺字段则拒绝。"""
    if 原生类型(值) is 原生列表 or not 有朴素对象原型(值):#数组或非朴素
        return None#拒绝
    键列表=可枚举字符串键(值)#可见键
    if 键列表 is None:#非法
        return None#拒绝
    if 值['kind']=='array' if 'kind' in 值 else None:#数组标记
        if 原生长度(键列表)!=2 or not 键含有(键列表,'kind') or not 键含有(键列表,'length'):#字段不对
            return None#拒绝
        长度=值['length']#长度
        if 原生类型(长度) is bool:#布尔不是整数
            return None#拒绝
        if 原生类型(长度) is int and 长度>=0:#合法长度
            return {'kind':'array','length':长度}#数组标记
        return None#拒绝
    if 值['kind']=='object' if 'kind' in 值 else None:#对象标记
        if 原生长度(键列表)!=2 or not 键含有(键列表,'kind') or not 键含有(键列表,'keys'):#字段不对
            return None#拒绝
        对象键=值['keys']#键表
        if 原生类型(对象键) is not 原生列表 or not 是稠密数组(对象键):#键表非法
            return None#拒绝
        唯一=原生集合()#去重
        规范化=[]#规范化键
        for 键 in 对象键:#逐键
            if 原生类型(键) is not str or 键 in 唯一:#非串或重复
                return None#拒绝
            唯一.add(键)#记下
            规范化.append(键)#收下
        return {'kind':'object','keys':规范化}#对象标记
    return None#未知 kind

def 解码ptcjson线(输入):#从扁平线重建无损 JSON
    """从扁平进程线格式重建一个无损 JSON 值。畸形或不完整流量返回空；遍历迭代，因此与应用嵌套深度无关。输入是未信任的报文。返回分离 JSON 值；线非法时为空。"""
    try:#畸形流量收成空
        if 原生类型(输入) is not 原生列表 or not 是稠密数组(输入) or 原生长度(输入)==0:#不是非空稠密数组
            return None#拒绝
        帧表=[]#容器帧
        根=[None]#根值
        根已写=[False]#根是否已写
        def 挂上(值):#把值挂到当前帧
            """把值挂到当前帧或根。"""
            if 原生长度(帧表)==0:#无父
                if 根已写[0]:#根已写
                    return False#拒绝
                根[0]=值#写根
                根已写[0]=True#已写
                return True#成功
            父=帧表[原生长度(帧表)-1]#当前帧
            上限=父['length'] if 父['kind']=='array' else 原生长度(父['keys'])#容量
            if 父['index']>=上限:#已满
                return False#拒绝
            if 父['kind']=='array':#数组
                父['target'].append(值)#追加
            else:#对象
                键=父['keys'][父['index']]#键
                父['target'][键]=值#写属性
            父['index']+=1#推进
            return True#成功
        for 记号下标 in range(原生长度(输入)):#逐记号
            记号=输入[记号下标]#当前记号
            帧=None#待压帧
            if 记号 is None or 原生类型(记号) is bool or 原生类型(记号) is str:#标量
                值=记号#原样
            elif 原生类型(记号) in (int,float) and 原生类型(记号) is not bool:#数字
                if not math.isfinite(记号):#非有限
                    return None#拒绝
                if 记号==0.0 and math.copysign(1.0,记号)<0:#负零
                    return None#拒绝
                值=记号#数字
            else:#容器
                if 原生类型(记号) is not 原生字典:#非对象
                    return None#拒绝
                标记=容器标记(记号)#解析标记
                if 标记 is None:#非法标记
                    return None#拒绝
                剩余=原生长度(输入)-记号下标-1#后面还有多少记号
                if 标记['kind']=='array':#数组
                    if 标记['length']>剩余:#记号不够
                        return None#拒绝
                    目标=[]#新数组
                    值=目标#本值
                    if 标记['length']>0:#非空
                        帧={'kind':'array','target':目标,'length':标记['length'],'index':0}#数组帧
                else:#对象
                    if 原生长度(标记['keys'])>剩余:#记号不够
                        return None#拒绝
                    目标={}#新对象
                    值=目标#本值
                    if 原生长度(标记['keys'])>0:#非空
                        帧={'kind':'object','target':目标,'keys':标记['keys'],'index':0}#对象帧
            if not 挂上(值):#挂不上
                return None#拒绝
            if 帧 is not None:#有新帧
                帧表.append(帧)#压栈
            while 原生长度(帧表)>0:#弹出已满帧
                现在=帧表[原生长度(帧表)-1]#顶帧
                上限=现在['length'] if 现在['kind']=='array' else 原生长度(现在['keys'])#容量
                if 现在['index']<上限:#未满
                    break#等更多记号
                帧表.pop()#弹出
        return 根[0] if 原生长度(帧表)==0 else None#帧必须耗尽
    except (节点ptc错误,TypeError,KeyError,IndexError,ValueError):#畸形
        return None#拒绝

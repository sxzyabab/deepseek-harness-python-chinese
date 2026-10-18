'对话表的顺序跟根引用和分组成员走，不跟行里的数据走'

from ......客户端.模块.客户端.通告 import 取握手窗口
from ......客户端.存储 import 创建快照存储#表格顺序
from ..格式 import 检查器预览#行摘要
from ..表格模型 import 检查器记录源#节点或分组的记录投影
from .对象 import 聊天对象索引#详情里的对象身份
from .选取匹配 import 匹配聊天节点行#点选对到行

列字段=('key','kind')#摘要里不再重复表格已经显示的列

class 聊天节点模型:
    '看结构变化。可见行再各自看自己的节点或分组'
    def __init__(自身,绑定):
        '绑定是被检查会话已有的对话'
        自身.绑定=绑定#对话绑定
        自身.行仓=创建快照存储(())#稳定的空顺序
        自身.源={}#行键到记录源
        自身.分组停={}#分组键到退订
        自身.条目=None#上一份分组根
        自身.顺序=None#上一份节点顺序
        自身.键列表=None#上一份节点键
        自身.锚列表=None#上一份锚序号
        自身.节点仓=None#上一份节点仓库
        自身.分组视图=None#上一份分组存储
        自身.订阅数=0#正在看的人数
        自身.断开=None#快照退订
        自身.已排队=False#微任务还没跑
        自身.目标={}#行键到对话坐标
        自身.索引=聊天对象索引(绑定)#对象身份
        自身.行监听=[]#表格监听
        自身.记录停={}#记录源扇出
        自身.刷新()#先有第一份顺序

    def 对象(自身,会话标识):
        '把对象引用和发布更新绑到这个会话'
        def 引用(值):
            '按原对象找命名引用，并补上表格行键'
            找到=自身.索引.引用(值)#索引
            if 找到 is None:#没登记
                return None#没有
            行=None#对应的表格行
            for 键,坐标 in 自身.目标.items():#当前行
                目标=找到['target']#引用坐标
                if 目标.get('nodeKey') is not None:#节点引用
                    if 坐标.get('nodeKey')==目标.get('nodeKey') and (目标.get('groupPart') is None or 坐标.get('groupPart')==目标.get('groupPart')):#节点和部位
                        行=(键,坐标)#命中
                        break#停
                elif 目标.get('groupKey') is not None and 坐标.get('groupKey')==目标.get('groupKey'):#分组引用
                    行=(键,坐标)#命中
                    break#停
            结果=dict(找到)#拷贝
            if 行 is not None:#对上了行
                结果['rowKey']=行[0]#行键
            return 结果#引用
        def 行(键):
            '这一行的引用，坐标用表格上的那一份'
            仓=自身.行(键)#记录源
            快照=None if 仓 is None else 仓.getSnapshot()#记录
            值=None if not isinstance(快照,dict) else 快照.get('value')#原值
            if 值 is None or isinstance(值,(str,int,float,bool)):#不是对象
                return None#没有
            找到=引用(值)#命名引用
            坐标=自身.目标.get(键)#这一行的坐标
            if 找到 is None or 坐标 is None:#对不上
                return None#没有
            结果=dict(找到)#拷贝
            结果['rowKey']=键#就是这一行
            结果['target']=坐标#用行坐标
            return 结果#引用
        return {'sessionId':会话标识,'updates':自身.绑定.snapshot,'reference':引用,'row':行}#对象表

    def getSnapshot(自身):
        '当前铺平的分组和节点顺序'
        return 自身.行仓.getSnapshot()#行列表

    def 选取(自身,目标):
        '在当前表里匹配，折叠的子行也算'
        自身.刷新(True)#先对齐
        return 匹配聊天节点行(目标,自身.目标)#最近的行

    def subscribe(自身,监听):
        '第一个订阅者激活聊天，并开始看快照'
        停行=自身.行仓.subscribe(监听)#结构
        首次=自身.订阅数==0#从无到有
        自身.订阅数=自身.订阅数+1#加上
        if 首次:#开始看
            def 快照变了():
                '对话快照变了就重算顺序'
                自身.刷新()#不强制时相同发布会跳过
            自身.断开=自身.绑定.snapshot.subscribe(快照变了)#订快照
            自身.绑定.activate('chat')#激活聊天目标
            自身.刷新(True)#强制对齐
        自身.行监听.append(监听)#记录变化也通知
        for 源 in 自身.源.values():#已有行
            自身.接记录(源)#扇出
        def 退订():
            '最后一个人离开时拆快照和分组订阅'
            停行()#行仓
            自身.订阅数=自身.订阅数-1#减一
            if 监听 in 自身.行监听:#还在
                自身.行监听.remove(监听)#卸掉
            if 自身.订阅数==0:#没人看
                if 自身.断开 is not None:#有快照订阅
                    自身.断开()#拆
                自身.断开=None#清空
                for 停 in 自身.分组停.values():#分组
                    停()#拆
                自身.分组停.clear()#清空
                for 停 in 自身.记录停.values():#记录扇出
                    停()#拆
                自身.记录停.clear()#清空
        return 退订#交给钩子

    def 行(自身,键):
        '已加载的行才有记录源。不因此增加订阅'
        return 自身.源.get(键)#没有就是 None

    def 接记录(自身,源):
        '节点或分组的值变了也让表格重画'
        if 自身.订阅数==0:#没人看
            return#不订
        标识=id(源)#源身份
        if 标识 in 自身.记录停:#订过
            return#不重复
        def 转发():
            '通知表格'
            for 回调 in list(自身.行监听):#每个监听
                回调()#重画
        自身.记录停[标识]=源.subscribe(转发)#退订

    def 刷新(自身,强制=False):
        '节点顺序、锚或分组根变了才重排。分组存储换代时丢掉旧源'
        快照=自身.绑定.snapshot.getSnapshot()#会话快照
        视图=快照.get('views') if isinstance(快照,dict) else 快照.views#视图存储
        聊天=视图.get('chat')#聊天快照
        分组=视图.grouped('chat')#分组存储
        节点=None#当前节点数组
        if isinstance(聊天,dict) and 聊天.get('nodes') is not None:#有仓库
            节点=聊天['nodes'].values()#节点列表
        if 节点 is None:#没有节点
            同键=自身.键列表 is None#以前也没有才算没变
        else:#有节点
            同键=自身.键列表 is not None and 自身.锚列表 is not None and len(节点)==len(自身.键列表)#长度相同
            if 同键:#再比键和锚
                for 下标,一项 in enumerate(节点):#逐个
                    if 一项.get('key')!=自身.键列表[下标] or 一项.get('anchorSeq')!=自身.锚列表[下标]:#变了
                        同键=False#需要重排
                        break#停
        顺序=聊天.get('order') if isinstance(聊天,dict) else None#可见顺序
        分组条目=None if 分组 is None else 分组.entries#分组根
        节点仓=聊天.get('nodes') if isinstance(聊天,dict) else None#仓库身份
        if not 强制 and 顺序 is 自身.顺序 and 节点仓 is 自身.节点仓 and 同键 and 分组 is 自身.分组视图 and 分组条目 is 自身.条目:#发布没变
            return#跳过
        自身.顺序=顺序#记下
        自身.条目=分组条目#记下
        if 节点 is None:#没有节点
            自身.键列表=None#清空
            自身.锚列表=None#清空
        else:#记下键和锚
            自身.键列表=[一项.get('key') for 一项 in 节点]#键
            自身.锚列表=[一项.get('anchorSeq') for 一项 in 节点]#锚
        if 分组 is not 自身.分组视图:#分组存储换了
            for 停 in 自身.分组停.values():#旧订阅
                停()#拆
            自身.分组停.clear()#清空
            自身.源.clear()#记录源也换
            自身.记录停.clear()#旧扇出不再用
        自身.分组视图=分组#当前分组
        if isinstance(聊天,dict) and 聊天.get('nodes') is not 自身.节点仓:#节点仓库换了
            自身.源.clear()#旧节点源作废
            自身.记录停.clear()#扇出作废
        自身.节点仓=节点仓#当前仓库
        活动分组=set()#这次还在的分组
        自身.目标.clear()#坐标重写
        行列表=[]#新顺序

        def 加节点(条目,父=None):
            '放一个节点行，并在还没有源时接上节点投影'
            键='node:'+str(条目.get('key'))+':'+str(条目.get('groupPart') or '')#部位不同是不同行
            位置=None#节点位置
            if isinstance(聊天,dict) and 聊天.get('nodes') is not None:#有仓库
                节点值=聊天['nodes'].get(条目.get('key'))#节点
                if isinstance(节点值,dict):#是节点
                    位置=节点值.get('location')#位置
            回合=None#回合号
            步=None#步骤号
            if isinstance(位置,dict) and 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict):#有回合
                回合=位置['turn'].get('turn')#回合
            if isinstance(位置,dict) and 位置.get('kind')=='step' and isinstance(位置.get('step'),dict):#有步骤
                步=位置['step'].get('step')#步骤
            坐标={'nodeKey':条目.get('key')}#节点键
            if 条目.get('groupPart') is not None:#有部位
                坐标['groupPart']=条目.get('groupPart')#部位
            if 回合 is not None:#有回合
                坐标['turn']=回合#回合
            if 步 is not None:#有步骤
                坐标['step']=步#步骤
            自身.目标[键]=坐标#记下
            行={'key':键,'depth':0 if 父 is None else 1}#深度
            if 父 is not None:#在分组里
                行['parent']=父#父键
            行列表.append(行)#放入顺序
            if 键 not in 自身.源 and isinstance(聊天,dict) and 聊天.get('nodes') is not None:#还没有投影
                部位=条目.get('groupPart')#闭包里的部位
                def 投影(节点,组分=部位):
                    '节点预览。有部位时身份带上部位'
                    节点位置=节点.get('location') if isinstance(节点,dict) else None#位置
                    if isinstance(节点位置,dict) and 节点位置.get('kind')=='step' and isinstance(节点位置.get('turn'),dict) and isinstance(节点位置.get('step'),dict):#步骤
                        地点=str(节点位置['turn'].get('turn'))+'/'+str(节点位置['step'].get('step'))#回合/步骤
                    elif isinstance(节点位置,dict) and 节点位置.get('kind')=='turn' and isinstance(节点位置.get('turn'),dict):#回合
                        地点=str(节点位置['turn'].get('turn'))#回合
                    elif isinstance(节点位置,dict):#其他位置
                        地点=str(节点位置.get('kind') or '')#种类
                    else:#没有位置
                        地点=''#空
                    记录={'type':节点.get('kind'),'identity':节点.get('key'),'location':地点,'value':节点,'summary':检查器预览(节点,列字段)}#预览
                    if 组分 is not None:#分组部位
                        记录=dict(记录)#拷贝
                        记录['identity']=str(节点.get('key'))+'#'+str(组分)#带部位
                    return 记录#记录
                源=检查器记录源(聊天['nodes'].source(条目.get('key')),投影)#按键投影
                自身.源[键]=源#留下
                自身.接记录(源)#有人看就扇出

        根条目=分组条目#优先分组根
        if 根条目 is None and isinstance(聊天,dict) and isinstance(聊天.get('order'),list):#没有分组就用顺序
            根条目=[{'kind':'node','key':键} for 键 in 聊天.get('order')]#节点根
        if 根条目 is None:#什么都没有
            根条目=[]#空
        已含=set()#已经出现在根或成员里的节点
        锚点=[]#每个根条目的最小锚
        for 根 in 根条目:#先算锚，好插入没列出的节点
            if isinstance(根,dict) and 根.get('kind')=='node':#单个节点
                成员=[根]#就它
            elif 分组 is not None and isinstance(根,dict):#分组
                组快照=分组.组源(根.get('key'))['getSnapshot']()#当前组
                成员=组快照.get('members') if isinstance(组快照,dict) else []#成员
            else:#无法识别
                成员=[]#空
            锚=None#最小锚
            for 成员项 in 成员 or []:#每个成员
                if not isinstance(成员项,dict):#不是引用
                    continue#跳过
                已含.add(成员项.get('key'))#算列出了
                序号=None#锚
                if isinstance(聊天,dict) and 聊天.get('nodes') is not None:#有节点
                    节点值=聊天['nodes'].get(成员项.get('key'))#节点
                    if isinstance(节点值,dict):#有
                        序号=节点值.get('anchorSeq')#锚
                if 序号 is not None:#有锚
                    锚=序号 if 锚 is None else min(锚,序号)#取更小
            锚点.append(锚)#这个根的锚
        未列=[]#顺序里没有、但节点仓库里有的
        for 一项 in 节点 or []:#全部节点
            if 一项.get('key') not in 已含:#没被根引用
                未列.append(一项)#待插入
        def 未列键(项):
            '先按锚序号，再按节点键'
            return (项.get('anchorSeq') or 0,str(项.get('key')))#排序键
        未列.sort(key=未列键)#锚然后键
        未列下标=0#下一个未列节点

        def 补未列(锚):
            '把锚不大于界限的未列节点插到当前位置'
            nonlocal 未列下标
            while 未列下标<len(未列):#还有
                一项=未列[未列下标]#下一个
                if 锚 is not None and (一项.get('anchorSeq') or 0)>锚:#还没到这个锚
                    break#停
                加节点({'key':一项.get('key')})#作为根节点
                未列下标=未列下标+1#推进

        for 下标,根 in enumerate(根条目):#按根顺序
            锚=锚点[下标] if 下标<len(锚点) else None#这个根的锚
            if 锚 is not None:#有锚才把更早的未列节点放前面
                补未列(锚)#插到这个根之前
            if not isinstance(根,dict):#坏条目
                continue#跳过
            if 根.get('kind')=='node':#节点根
                加节点(根)#放节点
                continue#下一个根
            活动分组.add(根.get('key'))#这组还在
            键='group:'+str(根.get('key'))#分组行
            自身.目标[键]={'groupKey':根.get('key')}#分组坐标
            源=分组.组源(根.get('key'))#分组源
            组=源['getSnapshot']()#当前组
            行列表.append({'key':键,'depth':0})#分组头
            if 键 not in 自身.源:#还没有投影
                def 投影组(值,组键=键):
                    '分组预览'
                    return {'type':'group','identity':值.get('key'),'location':'','value':值,'summary':检查器预览(值,列字段)}#分组记录
                记录源=检查器记录源(源,投影组)#投影
                自身.源[键]=记录源#留下
                自身.接记录(记录源)#扇出
            for 成员 in (组.get('members') if isinstance(组,dict) else []) or []:#成员
                if isinstance(成员,dict):#是引用
                    加节点(成员,键)#作为子行
            if 自身.订阅数>0 and 根.get('key') not in 自身.分组停:#还没订这组
                持有={'成员':组.get('members') if isinstance(组,dict) else None}#上一份成员
                def 成员变了(持有=持有,组源=源):
                    '成员身份变了才重排'
                    下一=组源['getSnapshot']()#新快照
                    下一成员=下一.get('members') if isinstance(下一,dict) else None#新成员
                    if 下一成员 is 持有['成员']:#同一份
                        return#不用排
                    持有['成员']=下一成员#记下
                    自身.安排()#下一拍重排
                自身.分组停[根.get('key')]=源['subscribe'](成员变了)#订分组
        补未列(None)#剩下的未列节点
        for 组键,停 in list(自身.分组停.items()):#不再出现的分组
            if 组键 not in 活动分组:#这次没有
                停()#拆
                del 自身.分组停[组键]#忘掉
        行键=set(行['key'] for 行 in 行列表)#当前行
        for 键 in list(自身.源.keys()):#旧源
            if 键 not in 行键:#行没了
                停=自身.记录停.pop(id(自身.源[键]),None)#扇出
                if 停 is not None:#订过
                    停()#拆
                del 自身.源[键]#丢掉
        自身.行仓.set(行列表)#发布顺序

    def 安排(自身):
        '同一拍里的多次成员变化只重排一次'
        if 自身.已排队:#已经排了
            return#等这一拍
        自身.已排队=True#占住
        def 到点():
            '微任务里重排。已经没人看就不再做'
            自身.已排队=False#放开
            if 自身.订阅数>0:#还有表格
                自身.刷新(True)#强制重排
        取握手窗口().queueMicrotask(到点)#排到微任务

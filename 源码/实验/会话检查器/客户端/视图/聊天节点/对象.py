'按对象身份索引节点、分组、回合和步骤，以及它们的数据读取'

class 聊天对象索引:
    '每一份已发布的对象只登记一次，不留住被换掉的发布'
    def __init__(自身,绑定):
        '绑定是这个会话已有的对话读取'
        自身.绑定=绑定#对话绑定
        自身.身份={}#对象身份到引用
        自身.已索引=set()#已经扫过的发布身份

    def 引用(自身,值):
        '按原对象身份查找。换代后的旧身份只要还被拿着就能找到'
        自身.刷新()#先补上当前发布
        if 值 is None or isinstance(值,(str,int,float,bool)):#不是对象
            return None#没有引用
        return 自身.身份.get(id(值))#按身份

    def 对话(自身):
        '当前聊天快照。还没激活时没有'
        快照=自身.绑定.snapshot.getSnapshot()#会话快照
        视图=快照.get('views') if isinstance(快照,dict) else 快照.views#视图存储
        return 视图.get('chat')#聊天快照

    def 登记(自身,值,引用):
        '只登记对象，并且同一身份不覆盖'
        if 值 is None or isinstance(值,(str,int,float,bool)):#标量
            return#不登记
        标识=id(值)#身份
        if 标识 not in 自身.身份:#第一次
            自身.身份[标识]=引用#留下

    def 位置(自身,值,步=None):
        '登记回合或步骤，以及它们的 data'
        回合体=值.get('turn') if isinstance(值,dict) else None#回合体
        回合号=回合体.get('turn') if isinstance(回合体,dict) else 值.get('turn') if isinstance(值,dict) else None#回合号
        if 步 is None:#回合
            身份文本=str(回合号)#回合文本
            种类='turn'#回合
        else:#步骤
            身份文本=str(回合号)+'/'+str(步)#回合/步骤
            种类='step'#步骤
        def 读取():
            '再读当前时间线上的这一份'
            聊天=自身.对话()#当前聊天
            时间线=聊天.get('timeline') if isinstance(聊天,dict) else None#时间线
            回合表=时间线.get('turns') if isinstance(时间线,dict) else {}#回合表
            当前=回合表.get(回合号) if isinstance(回合表,dict) else None#当前回合
            if 步 is None:#要回合
                return 当前#回合
            步骤=当前.get('steps') if isinstance(当前,dict) else None#步骤列表
            if not isinstance(步骤,list):#没有步骤
                return None#没了
            for 一项 in 步骤:#找这一步
                if isinstance(一项,dict) and 一项.get('step')==步:#同一步
                    return 一项#步骤
            return None#没了
        聊天=自身.对话()#当前聊天
        位置表=聊天.get('locations') if isinstance(聊天,dict) else None#位置索引
        首节点=None#这个范围的第一个节点
        if 位置表 is not None:#有索引
            if 步 is None:#回合
                键列表=位置表.getTurn(回合号)#回合节点
            else:#步骤
                键列表=位置表.getStep(回合号,步)#步骤节点
            if isinstance(键列表,(list,tuple)) and len(键列表)>0:#有节点
                首节点=键列表[0]#第一个
        坐标={'turn':回合号}#回合
        if 首节点 is not None:#有节点
            坐标['nodeKey']=首节点#第一个节点
        自身.登记(值,{'id':种类+':'+身份文本,'kind':种类,'identity':身份文本,'target':坐标,'read':读取})#范围本身
        数据=值.get('data') if isinstance(值,dict) else None#数据
        数据种类='turnData' if 步 is None else 'stepData'#数据种类
        def 读数据():
            '再读当前 data'
            当前=读取()#当前范围
            if not isinstance(当前,dict):#没了
                return None#没有数据
            return 当前.get('data')#数据
        自身.登记(数据,{'id':种类+'-data:'+身份文本,'kind':数据种类,'identity':身份文本,'target':坐标,'read':读数据})#数据

    def 刷新(自身):
        '节点数组、时间线和分组快照各只索引一次'
        聊天=自身.对话()#当前聊天
        if not isinstance(聊天,dict):#还没有聊天
            return#不用索引
        节点仓=聊天.get('nodes')#节点仓库
        节点=() if 节点仓 is None else 节点仓.values()#当前节点数组
        节点标识=id(节点)#这份数组
        if 节点标识 not in 自身.已索引:#新的一份节点
            自身.已索引.add(节点标识)#记过
            for 一项 in 节点:#每个节点
                键=一项.get('key')#节点键
                位置=一项.get('location') if isinstance(一项.get('location'),dict) else {}#位置
                回合=None#回合号
                if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict):#有回合
                    回合=位置['turn'].get('turn')#回合号
                坐标={'nodeKey':键}#节点坐标
                if 回合 is not None:#有回合
                    坐标['turn']=回合#写上
                def 读节点(节点键=键):
                    '再读这个键的当前节点'
                    当前=自身.对话()#当前聊天
                    仓=None if not isinstance(当前,dict) else 当前.get('nodes')#仓库
                    if 仓 is None:#没有
                        return None#没了
                    return 仓.get(节点键)#当前节点
                自身.登记(一项,{'id':'node:'+str(键),'kind':'node','identity':键,'target':dict(坐标),'read':读节点})#节点
                def 读数据(节点键=键):
                    '再读这个节点的 data'
                    当前聊天=自身.对话()#当前聊天
                    仓=None if not isinstance(当前聊天,dict) else 当前聊天.get('nodes')#仓库
                    当前=None if 仓 is None else 仓.get(节点键)#当前节点
                    if not isinstance(当前,dict):#没了
                        return None#没有
                    return 当前.get('data')#数据
                自身.登记(一项.get('data'),{'id':'node-data:'+str(键),'kind':'nodeData','identity':键,'target':dict(坐标),'read':读数据})#数据
        时间线=聊天.get('timeline')#时间线
        if 时间线 is not None and id(时间线) not in 自身.已索引:#新的时间线
            自身.已索引.add(id(时间线))#记过
            回合表=时间线.get('turns') if isinstance(时间线,dict) else {}#回合
            if isinstance(回合表,dict):#字典
                for 回合值 in 回合表.values():#每个回合
                    if not isinstance(回合值,dict):#不是对象
                        continue#跳过
                    自身.位置(回合值)#回合
                    for 步骤 in 回合值.get('steps') or []:#每个步骤
                        if isinstance(步骤,dict):#是对象
                            自身.位置(步骤,步骤.get('step'))#步骤
        快照=自身.绑定.snapshot.getSnapshot()#会话快照
        视图=快照.get('views') if isinstance(快照,dict) else 快照.views#视图
        分组=视图.grouped('chat')#聊天分组
        for 条目 in (分组.entries if 分组 is not None else ()):#根条目
            if not isinstance(条目,dict) or 条目.get('kind')!='group':#不是分组
                continue#跳过
            键=条目.get('key')#分组键
            源=分组.组源(键)#这一组的源
            组=源['getSnapshot']()#当前快照
            if not isinstance(组,dict) or id(组) in 自身.已索引:#没有或索引过
                continue#跳过
            自身.已索引.add(id(组))#记过
            坐标={'groupKey':键}#分组坐标
            def 读组(组键=键,分组存储=分组):
                '再读这一组'
                当前快照=自身.绑定.snapshot.getSnapshot()#最新会话
                当前视图=当前快照.get('views') if isinstance(当前快照,dict) else 当前快照.views#视图
                当前分组=当前视图.grouped('chat')#分组
                if 当前分组 is None:#没有
                    return None#没了
                return 当前分组.组源(组键)['getSnapshot']()#当前组
            自身.登记(组,{'id':'group:'+str(键),'kind':'group','identity':键,'target':坐标,'read':读组})#分组
            def 读组数据(组键=键):
                '再读分组 data'
                当前快照=自身.绑定.snapshot.getSnapshot()#最新会话
                当前视图=当前快照.get('views') if isinstance(当前快照,dict) else 当前快照.views#视图
                当前分组=当前视图.grouped('chat')#分组
                当前=None if 当前分组 is None else 当前分组.组源(组键)['getSnapshot']()#当前组
                if not isinstance(当前,dict):#没了
                    return None#没有
                return 当前.get('data')#数据
            自身.登记(组.get('data'),{'id':'group-data:'+str(键),'kind':'groupData','identity':键,'target':坐标,'read':读组数据})#数据
            for 成员 in 组.get('members') or []:#成员引用
                if not isinstance(成员,dict):#不是引用
                    continue#跳过
                节点键=成员.get('key')#节点键
                成员坐标={'nodeKey':节点键}#成员坐标
                if 成员.get('groupPart') is not None:#有部位
                    成员坐标['groupPart']=成员.get('groupPart')#部位
                def 读成员(成员键=节点键):
                    '再读成员节点'
                    当前=自身.对话()#当前聊天
                    仓=None if not isinstance(当前,dict) else 当前.get('nodes')#仓库
                    if 仓 is None:#没有
                        return None#没了
                    return 仓.get(成员键)#节点
                自身.登记(成员,{'id':'node:'+str(节点键),'kind':'node','identity':节点键,'target':成员坐标,'read':读成员})#成员引用

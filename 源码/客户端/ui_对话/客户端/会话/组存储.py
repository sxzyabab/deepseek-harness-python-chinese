from ....存储 import 创建快照存储
from .....工具.值 import 断言永不
from ..约定.槽 import 对话错误

__all__=['会话组存储']

def 同节点引用(左,右):
    """键与组分都相同。"""
    左组分=左['groupPart'] if 'groupPart' in 左 else None
    右组分=右['groupPart'] if 'groupPart' in 右 else None
    return 左['key']==右['key'] and 左组分==右组分

def 同条目(左,右):
    """根引用种类与键相同；节点还比组分。"""
    if 左['kind']!=右['kind'] or 左['key']!=右['key']:
        return False
    if 左['kind']=='group':
        return True
    左组分=左['groupPart'] if 'groupPart' in 左 else None
    右组分=右['groupPart'] if 'groupPart' in 右 else None
    return 左组分==右组分

def 复用引用(先前,其后,相等):
    """逐项相等则保留先前数组身份。"""
    if 先前 is 其后:
        return 先前
    if len(先前)==len(其后):
        下标=0
        全等=True
        while 下标<len(先前):
            if not 相等(先前[下标],其后[下标]):
                全等=False
                break
            下标+=1
        if 全等:
            return 先前
    return 其后

class 会话组存储:
    """带键分组发布与渲染位置增量校验。"""
    def __init__(自身):
        """空根序列。"""
        自身.根=()
        自身.根组=set()
        自身.组表={}
        自身.放置={}
        自身.源表={}
        自身.脏=set()

    @property
    def entries(自身):
        """身份稳定的有序根引用。"""
        return 自身.根

    def 组源(自身,键):
        """观察一组而不订阅根序列。"""
        if 键 in 自身.源表:
            return 自身.源表[键]['observable']
        发布=创建快照存储(自身.组表[键] if 键 in 自身.组表 else None)
        def 取快照():
            """当前组快照。"""
            return 自身.组表[键] if 键 in 自身.组表 else None
        可观察={'getSnapshot':取快照,'subscribe':发布.subscribe}
        自身.源表[键]={'publication':发布,'observable':可观察}
        return 可观察

    def 准备并安装(自身,更新,读节点):
        """安装一次已校验更新，不通知读者。更新为 dict。"""
        下一根=自身.根 if 'entries' not in 更新 else 复用引用(自身.根,更新['entries'],同条目)
        下一根组=自身.根组 if 下一根 is 自身.根 else 自身.收集根组(下一根)
        变更=自身.收集变更(更新)
        写入=变更['upserts']
        移除=变更['removes']
        替换引用=更新['groups']['kind']=='replace'
        新增数=0
        for 键 in 写入:
            if 键 not in 自身.组表:
                新增数+=1
        规模=len(自身.组表)-len(移除)+新增数
        if 规模!=len(下一根组):
            raise 对话错误('conversation group records and root references must correspond one-to-one')
        for 键 in 移除:
            if 键 in 下一根组:
                raise 对话错误('conversation group "'+str(键)+'" is still referenced')
        for 键 in 写入:
            if 键 not in 下一根组:
                raise 对话错误('conversation group "'+str(键)+'" has no root reference')
        if 下一根组 is not 自身.根组:
            for 键 in 下一根组:
                if 键 not in 写入 and 键 not in 自身.组表:
                    raise 对话错误('conversation root references missing group "'+str(键)+'"')
        受影响={}
        def 部分于(键):
            """取出或复制放置集合。"""
            if 键 not in 受影响:
                原=自身.放置[键] if 键 in 自身.放置 else set()
                受影响[键]=set(原)
            return 受影响[键]
        def 删引用(引用):
            """从放置去掉组分。"""
            部分于(引用['key']).discard(引用['groupPart'] if 'groupPart' in 引用 else None)
        def 加引用(引用):
            """校验节点存在且位置不重叠。"""
            if 读节点(引用['key']) is None:
                raise 对话错误('conversation group references missing Node "'+str(引用['key'])+'"')
            部分=部分于(引用['key'])
            组分=引用['groupPart'] if 'groupPart' in 引用 else None
            if 组分 in 部分 or (组分 is None and len(部分)>0) or None in 部分:
                raise 对话错误('conversation Node "'+str(引用['key'])+'" has overlapping rendering positions')
            部分.add(组分)
        if 替换引用 or 下一根 is not 自身.根:
            for 条目 in 自身.根:
                if 条目['kind']=='node':
                    删引用(条目)
        for 键 in 移除:
            for 成员 in 自身.组表[键]['members']:
                删引用(成员)
        for 键 in 写入:
            下一=写入[键]
            先前=自身.组表[键] if 键 in 自身.组表 else None
            if 先前 is not None and (替换引用 or 先前['members'] is not 下一['members']):
                for 成员 in 先前['members']:
                    删引用(成员)
        if 替换引用 or 下一根 is not 自身.根:
            for 条目 in 下一根:
                if 条目['kind']=='node':
                    加引用(条目)
        for 键 in 写入:
            下一=写入[键]
            旧成员=自身.组表[键]['members'] if 键 in 自身.组表 else None
            if 替换引用 or 旧成员 is not 下一['members']:
                for 成员 in 下一['members']:
                    加引用(成员)
        for 键 in 受影响:
            部分=受影响[键]
            if len(部分)==0:
                自身.放置.pop(键,None)
            else:
                自身.放置[键]=部分
        for 键 in 移除:
            del 自身.组表[键]
            自身.脏.add(键)
        for 键 in 写入:
            下一=写入[键]
            if 键 in 自身.组表 and 自身.组表[键] is 下一:
                continue
            自身.组表[键]=下一
            自身.脏.add(键)
        自身.根=下一根
        自身.根组=下一根组

    def 发布(自身):
        """相关目标数据安装后再发布已变组源。"""
        键表=list(自身.脏)
        自身.脏.clear()
        for 键 in 键表:
            if 键 in 自身.源表:
                自身.源表[键]['publication'].set(自身.组表[键] if 键 in 自身.组表 else None)

    def 清空(自身):
        """去掉分组但不删除源节点；发布仍推迟。"""
        def 空读(_键):
            """空替换从不读节点。"""
            return None
        自身.准备并安装({'entries':(),'groups':{'kind':'replace','snapshots':()}},空读)

    def 收集根组(自身,条目表):
        """根上的组键集合；重复引用失败。"""
        键集=set()
        for 条目 in 条目表:
            if 条目['kind']!='group':
                continue
            键=条目['key']
            if 键 in 键集:
                raise 对话错误('conversation group "'+str(键)+'" has duplicate root references')
            键集.add(键)
        return 键集

    def 收集变更(自身,更新):
        """在安装前校验完整批次。"""
        写入={}
        移除=set()
        def 加入(快照):
            """去重写入并复用成员数组。"""
            键=快照['key']
            if 键 in 写入:
                raise 对话错误('conversation group "'+str(键)+'" has duplicate upserts')
            先前=自身.组表[键] if 键 in 自身.组表 else None
            if 先前 is None:
                写入[键]=快照
                return
            成员=复用引用(先前['members'],快照['members'],同节点引用)
            if 先前['data'] is 快照['data'] and 先前['members'] is 成员:
                写入[键]=先前
            else:
                下=dict(快照)
                下['members']=成员
                写入[键]=下
        种=更新['groups']['kind']
        if 种=='replace':
            for 快照 in 更新['groups']['snapshots']:
                加入(快照)
            for 键 in 自身.组表:
                if 键 not in 写入:
                    移除.add(键)
        elif 种=='apply':
            for 快照 in 更新['groups']['upserts']:
                加入(快照)
            for 键 in 更新['groups']['removes']:
                if 键 in 移除:
                    raise 对话错误('conversation group "'+str(键)+'" has duplicate removals')
                if 键 not in 自身.组表:
                    raise 对话错误('conversation group "'+str(键)+'" cannot be removed because it is absent')
                if 键 in 写入:
                    raise 对话错误('conversation group "'+str(键)+'" cannot be upserted and removed together')
                移除.add(键)
        else:
            断言永不(更新['groups'])
        return {'upserts':写入,'removes':移除}

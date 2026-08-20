"""一份智能体日志如何交代它已消费的工作。

对齐上游 `agent/src/consumed-work.ts`。公开面仅中文名；事件 type 与载荷字段键保持上游字面量。
"""
from typing import NotRequired,TypedDict#可选字段与结构类型

__all__=('已消费工作账本','交代领取','折叠已消费工作')#仅中文公开名

class 已消费工作账本(TypedDict):#一份智能体日志如何交代它已消费的工作
    """一份智能体日志如何交代它已消费的工作。"""
    end:NotRequired[object]#交代已消费工作的最近已关闭 turn/end；没有任何轮次因工作关闭时缺席
    droppedUnrun:bool#该轮次之后，已接受的工作是否被从收件箱取消且未运行

def 读(对象,名):#从映射或对象读取字段
    """从映射或对象读取字段。"""
    if isinstance(对象,dict):#映射
        return 对象[名]#映射键
    return getattr(对象,名)#对象属性

def 读可选(对象,名):#从映射或对象读取可选字段
    """从映射或对象读取可选字段。"""
    if isinstance(对象,dict):#映射
        return 对象.get(名)#映射键
    return getattr(对象,名,None)#对象属性

def 交代领取(原因):#结束是否交代领取
    """消费了输入但从未到达步骤的轮次，其结束是否交代那份输入。"""
    种类=读(原因,'kind')#结束种类
    if 种类=='completed':#正常完成
        return False#不交代被改写走的领取
    if 种类=='blocked':#预步骤拒绝
        return True#预步骤拒绝交代领取
    if 种类=='aborted':#中止
        return True#中止交代领取
    if 种类=='interrupted':#打断
        return True#打断交代领取
    if 种类=='error':#出错
        return True#出错交代领取
    return True#未列名结束不得读成成功

def 折叠已消费工作(事件们):#折叠已消费工作账本
    """把一份智能体日志或其拥有的后缀折成已消费工作账本。"""
    已进入步骤=set()#进入过步骤的轮次
    已领取=set()#领取过输入的轮次
    打开=None#当前打开的轮次
    结束=None#最近交代用的 turn/end
    丢掉未运行=False#之后是否有未运行丢掉
    for 事件 in 事件们:#扫描事件
        类型=读(事件,'type')#事件类型
        if 类型=='turn/start':#轮次开始
            打开=读(读(事件,'data'),'turn')#记下打开的轮次
            continue#处理完
        if 类型=='step/start':#步骤开始
            已进入步骤.add(读(读(事件,'data'),'turn'))#该轮次已进入步骤
            continue#处理完
        if 类型=='agent/inbox/spliced':#收件箱拼接
            数据=读(事件,'data')#拼接字段
            删除数=读可选(数据,'removedCount')#删除条数
            if 删除数 is None:#纯插入
                continue#纯插入不改变领取账
            插入=读(数据,'inserted')#插入列表
            if 读可选(数据,'outcome')=='canceled':#取消
                if len(插入)==0:#空插入
                    丢掉未运行=True#空插入的取消才算丢掉
            elif 打开 is not None:#打开轮次内的删除
                已领取.add(打开)#打开轮次内的删除记为领取
            continue#拼接处理完
        if 类型=='turn/end':#轮次结束
            数据=读(事件,'data')#结束字段
            轮次=读(数据,'turn')#结束轮次
            打开=None#轮次已关
            步骤命中=轮次 in 已进入步骤#是否进入过步骤
            if 步骤命中:#从步骤账摘掉
                已进入步骤.discard(轮次)#从步骤账摘掉
            领取命中=False#是否领取过
            if not 步骤命中:#查领取账
                领取命中=轮次 in 已领取#查领取账
                if 领取命中:#从领取账摘掉
                    已领取.discard(轮次)#从领取账摘掉
            if 步骤命中 or (领取命中 and 交代领取(读(数据,'reason'))):#该结束交代了工作
                结束=事件#记下交代结束
                丢掉未运行=False#本轮已交代此前丢掉
            continue#结束处理完
    账本={'droppedUnrun':丢掉未运行}#账本
    if 结束 is not None:#有交代轮次
        账本['end']=结束#有交代轮次才写入
    return 账本#返回账本

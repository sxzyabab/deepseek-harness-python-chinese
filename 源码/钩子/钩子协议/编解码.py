"""解码两种方言的钩子进程结果。退出码 0 可带结构化 JSON 或纯 stdout；退出码 2 用 stderr 作为原因阻断；其余退出码为非阻断错误。桥接层决定哪些已识别字段生效。"""
import json#解析干净退出时的结构化 stdout

阻断退出码=2#发出阻断错误的退出码

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 读字符串(对象,键):#读取字符串字段
    """缺席或类型不对则返回 None。"""
    值=取字段(对象,键)#取出指定键的值
    return 值 if isinstance(值,str) else None#是字符串才返回

def 读布尔(对象,键):#读取布尔字段
    """缺席或类型不对则返回 None。"""
    值=取字段(对象,键)#取出指定键的值
    return 值 if isinstance(值,bool) else None#是布尔才返回

def 读对象(值):#读取普通对象
    """普通对象（非 None、非列表），否则 None。"""
    if isinstance(值,dict):#映射即普通对象
        return 值#断言为普通对象
    return None#否则缺席

def 顶层判定(值):#规范化顶层判定
    """遗留顶层 decision 只允许 approve/block。"""
    return 值 if 值=='approve' or 值=='block' else None#仅批准或阻断有效

def 专属判定(值):#规范化专属权限判定
    """permissionDecision 只允许 allow/deny/ask。"""
    return 值 if 值=='allow' or 值=='deny' or 值=='ask' else None#仅允许拒绝询问有效

def 折入结构化(输出,已解析,期望事件名=None):#折入结构化 stdout
    """把已解析的结构化 stdout 对象折入输出（原地修改）。"""
    继续=读布尔(已解析,'continue')#读取是否继续
    if 继续 is not None:#有值则写入
        输出['continue']=继续#写入
    停止原因=读字符串(已解析,'stopReason')#读取停止原因
    if 停止原因 is not None:#有值则写入
        输出['stopReason']=停止原因#写入
    系统消息=读字符串(已解析,'systemMessage')#读取系统消息
    if 系统消息 is not None:#有值则写入
        输出['systemMessage']=系统消息#写入
    顶层=顶层判定(读字符串(已解析,'decision'))#规范化顶层判定
    if 顶层 is not None:#有值则写入判定
        输出['decision']=顶层#写入
    顶层原因=读字符串(已解析,'reason')#读取顶层原因
    if 顶层原因 is not None:#有值则写入原因
        输出['reason']=顶层原因#写入
    专属=读对象(取字段(已解析,'hookSpecificOutput'))#读取钩子专属输出
    if 专属 is None:#不存在则结束
        return#结束
    事件名=读字符串(专属,'hookEventName')#读取事件名判别标签
    if 事件名 is not None:#有事件名则记录
        输出['hookEventName']=事件名#始终露出判别标签
    if 期望事件名 is not None and 事件名!=期望事件名:#事件名守卫未通过
        return#丢弃事件作用域字段
    权限=专属判定(读字符串(专属,'permissionDecision'))#规范化权限判定
    if 权限 is not None:#权限判定覆盖顶层判定
        输出['decision']=权限#覆盖
    权限原因=读字符串(专属,'permissionDecisionReason')#读取权限判定原因
    if 权限原因 is not None:#有值则覆盖原因
        输出['reason']=权限原因#覆盖
    附加=读字符串(专属,'additionalContext')#读取附加上下文
    if 附加 is not None:#有值则写入
        输出['additionalContext']=附加#写入
    更新输入=读对象(取字段(专属,'updatedInput'))#读取更新后的输入
    if 更新输入 is not None:#有值则写入
        输出['updatedInput']=更新输入#写入

def 解析钩子输出(退出码,标准输出,标准错误,期望事件名=None):#解码钩子进程输出
    """将进程输出解码为方言无关的钩子结果。畸形 JSON 仍当作纯 stdout。"""
    修剪错误=(标准错误 or '').strip()#去掉 stderr 两端空白
    修剪输出=(标准输出 or '').strip()#去掉 stdout 两端空白
    输出={'exitCode':退出码,'stderr':修剪错误,'stdout':修剪输出}#组装基础输出
    if 退出码==阻断退出码:#退出码 2 视为阻断
        输出['decision']='block'#写入阻断判定
        if len(修剪错误)>0:#有 stderr 则作为阻断原因
            输出['reason']=修剪错误#写入原因
    if 退出码==0:#仅干净退出才解析结构化输出
        if 修剪输出.startswith('{'):#以左花括号开头才当 JSON 对象
            已解析=None#结构化解析结果
            try:#尝试把 stdout 当 JSON 解析
                已解析=读对象(json.loads(修剪输出))#解析为普通对象
            except Exception:#吞掉畸形 JSON
                #干净退出时 JSON 畸形=无结构化输出。纯 stdout 仍留给桥接层。
                已解析=None#放弃结构化结果
            if 已解析 is not None:#有结构化对象则折入
                折入结构化(输出,已解析,期望事件名)#折入
    return 输出#返回解码结果

"""把命中的钩子收成最严格的一份结果。权限优先级是 deny > ask > allow；第一次 continue:false 的停止会粘住；胜出档位的原因会拼接；上下文和系统消息按钩子顺序累积。"""

合并判定=('allow','ask','deny','none')#合并后的判定

合并结果字段=('decision','reason','stop','stopReason','additionalContext','systemMessages')#合并后的钩子结果字段

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 严度(判定):#判定严度分
    """给单条钩子判定打分，供 deny>ask>allow 优先级使用（越高越严）。"""
    if 判定=='deny' or 判定=='block':#拒绝与阻断最严
        return 3#最严
    if 判定=='ask':#询问次之
        return 2#次严
    if 判定=='approve' or 判定=='allow':#批准与允许最松
        return 1#最松
    return 0#无判定

def 分值折回(最高分):#分值折回判定
    """把打分折回合并枚举。"""
    if 最高分==3:#最严为拒绝
        return 'deny'#拒绝
    if 最高分==2:#次严为询问
        return 'ask'#询问
    if 最高分==1:#有允许
        return 'allow'#允许
    return 'none'#无人表态

def 合并钩子输出(输出们):#合并命中钩子的输出
    """按优先级把输出们（命中某点的全部钩子结果，按钩子顺序）折成一份合并结果。空列表给出中性结果。"""
    最高=0#目前见到的最高严度
    档位原因={}#各档位的原因列表
    停止=False#是否已有人要求停止
    停止原因=None#首次停止原因
    附加上下文=[]#累积附加上下文
    系统消息们=[]#累积系统消息
    for 出 in 输出们:#按钩子顺序折入
        分=严度(取字段(出,'decision'))#本条严度
        if 分>最高:#刷新最高严度
            最高=分#更新
        原因=取字段(出,'reason')#本条原因
        if (分==3 or 分==2) and 原因 is not None and len(原因)>0:#拒绝/询问且有原因才收
            列表=档位原因.get(分)#该档位已有原因
            if 列表 is None:#尚未有列表
                列表=[]#新建
                档位原因[分]=列表#写回
            列表.append(原因)#追加本条原因
        if 取字段(出,'continue') is False and (not 停止):#第一次continue假则粘住停止
            停止=True#记下停止
            停因=取字段(出,'stopReason')#首次停止原因
            if 停因 is not None:#有停止原因
                停止原因=停因#记下
        附加=取字段(出,'additionalContext')#附加上下文
        if 附加 is not None and len(附加)>0:#有附加上下文则累积
            附加上下文.append(附加)#按序追加
        系统=取字段(出,'systemMessage')#系统消息
        if 系统 is not None and len(系统)>0:#有系统消息则累积
            系统消息们.append(系统)#按序追加
    原因们=档位原因.get(最高)#取出胜出档位的原因
    if 原因们 is None:#无人写原因
        原因们=[]#空列表
    结果={'decision':分值折回(最高),'stop':停止,'additionalContext':附加上下文,'systemMessages':系统消息们}#组装合并结果
    if len(原因们)>0:#有原因才写入拼接原因
        结果['reason']='\n\n'.join(原因们)#拼接
    if 停止原因 is not None:#有停止原因才写入
        结果['stopReason']=停止原因#写入
    return 结果#合并结果对象

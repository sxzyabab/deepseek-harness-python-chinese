"""把 Codex 的五个事件钩子子集解析成共用的 MatcherGroup。只跑同步命令钩子；其他类型和 async: true 的命令记为已跳过。Codex 不做命令替换。"""
from hook_protocol import 匹配诊断 as 匹配器诊断#按方言校验匹配器

科德克斯事件们=(#本桥支持的五个 Codex 钩子点
    'PreToolUse',#工具使用前
    'PostToolUse',#工具使用后
    'SessionStart',#会话开始
    'UserPromptSubmit',#用户提示提交
    'Stop',#停止
)#只读事件名列表

def 当作对象(值):#读取普通对象
    """普通对象（非 None、非列表），否则 None。"""
    if isinstance(值,dict):#映射即普通对象
        return 值#断言为普通对象
    return None#否则缺席

def 解析科德克斯配置(原始):#解析 Codex 钩子配置
    """解析带包装或裸的 Codex 事件图。未知事件和畸形条目忽略而不让启动失败；不支持或异步的钩子放进 skipped。UserPromptSubmit 和 Stop 上的 matcher 字段会丢掉，因为那些事件没有匹配主体。带 matcher 的可跑组若正则非法会抛 SyntaxError，让桥在登记监听器之前拒绝整份配置。"""
    配置={}#可跑的按事件分组
    已跳过=[]#被跳过的钩子
    根=当作对象(原始)#把原始值当对象
    if 根 is None:#没有根对象
        return {'config':配置,'skipped':已跳过}#空结果
    钩子图=当作对象(根.get('hooks'))#有 hooks 键用它
    if 钩子图 is None:#没有 hooks 包装
        钩子图=根#把根当事件图
    for 事件 in 科德克斯事件们:#只看支持的五个事件
        原始组们=钩子图.get(事件)#该事件的原始组列表
        if not isinstance(原始组们,list):#不是列表则跳过
            continue#下个事件
        组们=[]#该事件可跑的匹配组
        for 原始组 in 原始组们:#逐组解析
            组=当作对象(原始组)#组必须是对象
            if 组 is None or not isinstance(组.get('hooks'),list):#缺 hooks 列表则跳过
                continue#下一组
            命令们=[]#本组留下来的命令钩子
            for 原始钩子 in 组['hooks']:#逐条钩子
                钩子=当作对象(原始钩子)#钩子必须是对象
                if 钩子 is None:#非对象则跳过
                    continue#下一条
                类型=钩子.get('type') if isinstance(钩子.get('type'),str) else 'command'#缺 type 则当命令
                if 类型!='command':#非命令类型不跑
                    已跳过.append({'event':事件,'reason':'unsupported "'+类型+'" hook'})#记入已跳过
                    continue#下一条
                if 钩子.get('async') is True:#异步命令不跑
                    已跳过.append({'event':事件,'reason':'async hook'})#记入已跳过
                    continue#下一条
                if not isinstance(钩子.get('command'),str):#没有命令字符串则跳过
                    continue#下一条
                条目={'command':钩子['command']}#命令字符串（Codex 不做替换）
                if isinstance(钩子.get('timeout'),(int,float)) and not isinstance(钩子.get('timeout'),bool):#优先用 timeout
                    条目['timeoutSec']=钩子['timeout']#超时秒数
                elif isinstance(钩子.get('timeoutSec'),(int,float)) and not isinstance(钩子.get('timeoutSec'),bool):#否则用 timeoutSec 别名
                    条目['timeoutSec']=钩子['timeoutSec']#超时秒数别名
                命令们.append(条目)#收一条命令钩子
            if len(命令们)==0:#本组没有可跑命令则丢掉
                continue#下一组
            if 事件=='UserPromptSubmit' or 事件=='Stop':#这两类事件没有匹配主体
                匹配器=None#丢掉 matcher
            elif isinstance(组.get('matcher'),str):#否则字符串 matcher 才保留
                匹配器=组['matcher']#保留
            else:#非字符串
                匹配器=None#丢掉
            诊断=匹配器诊断(匹配器,'codex')#按 Codex 方言校验匹配器
            if 诊断 is not None:#非法正则拒绝整份配置
                raise SyntaxError(诊断+' on event '+repr(事件))#带事件名的诊断
            匹配组={'hooks':命令们}#本组命令钩子
            if 匹配器 is not None:#有 matcher 才写入
                匹配组['matcher']=匹配器#匹配模式
            组们.append(匹配组)#收一个匹配组
        if len(组们)>0:#该事件有可跑组才写入
            配置[事件]=组们#写入事件图
    return {'config':配置,'skipped':已跳过}#返回可跑配置与跳过列表

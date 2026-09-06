"""会话环境读数带：回合/步/时长/吞吐/缓存/令牌。

对齐上游 `ui-chat/src/client/chat/StatsLine.tsx`。公开面仅中文名。
节点、用量、统计为 dict。
"""
from .消息铬 import 格式化每秒令牌#吞吐数字
from .令牌格式 import 格式化令牌,格式化缓存命中百分比#令牌与缓存
from ..约定.回合指标 import 助手步骤读数#步骤读数

__all__=['派生统计','格式化时长','缓存命中百分','计费输入令牌','统计行']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 派生统计(节点列表):
    """无 sessionStats 投影时用。"""
    回合集=set()#回合
    步数=0#步
    模型毫秒=0#LLM
    工具毫秒=0#工具
    首令牌毫秒=0#TTFT 和
    首令牌步=0#TTFT 步数
    解码毫秒=0#解码
    解码令牌=0#产出
    序列=节点列表 if 节点列表 is not None else []#遍历
    for 节点 in 序列:#遍历
        种=节点['kind'] if 'kind' in 节点 else None#kind
        if 种=='tool-result':#工具结果
            调用时=节点['callTime'] if 'callTime' in 节点 else None#callTime
            if 调用时 is not None:#有
                时=节点['time'] if 'time' in 节点 and 节点['time'] is not None else 0#时
                工具毫秒+=max(0,时-调用时)#墙钟
            continue#下
        if 种!='assistant':#非助手
            continue#跳
        回合集.add(节点['turn'] if 'turn' in 节点 else None)#回合
        步数+=1#步
        计时=节点['timing'] if 'timing' in 节点 else None#计时
        if 计时 is not None and 'stepStartTime' in 计时 and 计时['stepStartTime'] is not None:#有步进
            完成=计时['completedTime'] if 'completedTime' in 计时 and 计时['completedTime'] is not None else 0#完成
            模型毫秒+=max(0,完成-计时['stepStartTime'])#LLM
        读数=助手步骤读数(节点)#读数
        if 'ttftMs' in 读数 and 读数['ttftMs'] is not None:#TTFT
            首令牌毫秒+=读数['ttftMs']#加
            首令牌步+=1#步
        if 'decodeMs' in 读数 and 读数['decodeMs'] is not None and 'outputTokens' in 读数 and 读数['outputTokens'] is not None:#吞吐样本
            解码毫秒+=读数['decodeMs']#加
            解码令牌+=读数['outputTokens']#加
    return {'turns':len(回合集),'steps':步数,'llmMs':模型毫秒,'toolMs':工具毫秒,'ttftMs':首令牌毫秒,'ttftSteps':首令牌步,'decodeMs':解码毫秒,'decodeTokens':解码令牌}#统计

def 格式化时长(毫秒,翻译):
    """45.2s / 2m42s。"""
    秒=毫秒/1000#秒
    if 秒<60:#亚分
        return 翻译('duration.compactSeconds',{'seconds':round(秒*10)/10})#秒
    整=round(秒)#整秒
    return 翻译('duration.compactMinutes',{'minutes':整//60,'seconds':整%60})#分秒

def 计费输入令牌(用量):
    """uncached+cacheRead+cacheWrite。用量为 dict。"""
    未=用量['uncachedInputTokens'] if 'uncachedInputTokens' in 用量 and 用量['uncachedInputTokens'] is not None else 0#未缓存
    读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 and 用量['cacheReadTokens'] is not None else 0#读
    写=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 and 用量['cacheWriteTokens'] is not None else 0#写
    return 未+读+写#和

def 缓存命中百分(用量):
    """委托格式化；无计费输入则 None。"""
    读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 and 用量['cacheReadTokens'] is not None else 0#读
    return 格式化缓存命中百分比(读,计费输入令牌(用量))#百分

def 取遗留节点(快照):
    """legacy.nodes。快照为 dict。"""
    遗留=快照['legacy'] if 'legacy' in 快照 else None#遗留
    if 遗留 is None or 'nodes' not in 遗留 or 遗留['nodes'] is None:#无
        return []#空
    return 遗留['nodes']#节点

class 统计行:
    """投影优先，窗口折叠回退。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """无组返回 None。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用聊天=属性['useChat'] if 'useChat' in 属性 else None#快照钩
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None#投影
        节点列表=用聊天(取遗留节点) if 用聊天 is not None else []#节点
        用量=用投影('tokenUsage') if 用投影 is not None else None#用量
        投影统计=用投影('sessionStats') if 用投影 is not None else None#投影
        统计=投影统计 if 投影统计 is not None else 派生统计(节点列表)#统计
        组列表=[]#组
        步=统计['steps'] if 'steps' in 统计 and 统计['steps'] is not None else 0#步
        if 步>0:#有步
            回合=统计['turns'] if 'turns' in 统计 else None#回合
            组列表.append(翻译('stats.counts',{'turns':回合,'steps':步}))#计数
            时长列表=[]#时长
            llm=统计['llmMs'] if 'llmMs' in 统计 and 统计['llmMs'] is not None else 0#LLM
            if llm>0:#LLM
                时长列表.append(翻译('stats.llm',{'duration':格式化时长(llm,翻译)}))#LLM
            工具=统计['toolMs'] if 'toolMs' in 统计 and 统计['toolMs'] is not None else 0#工具
            if 工具>0:#工具
                时长列表.append(翻译('stats.toolCall',{'duration':格式化时长(工具,翻译)}))#工具
            if len(时长列表)>0:#有
                组列表.append(' · '.join(时长列表))#时长组
            速率列表=[]#速
            首步=统计['ttftSteps'] if 'ttftSteps' in 统计 and 统计['ttftSteps'] is not None else 0#TTFT 步
            if 首步>0:#平均 TTFT
                ttft=统计['ttftMs'] if 'ttftMs' in 统计 else 0#TTFT
                速率列表.append(翻译('stats.ttftAverage',{'duration':格式化时长(ttft/首步,翻译)}))#TTFT
            解码=统计['decodeMs'] if 'decodeMs' in 统计 and 统计['decodeMs'] is not None else 0#解码
            if 解码>0:#吞吐
                令牌=统计['decodeTokens'] if 'decodeTokens' in 统计 else 0#令牌
                速率列表.append(翻译('stats.tokensPerSecond',{'throughput':格式化每秒令牌(令牌/(解码/1000))}))#吞吐
            if len(速率列表)>0:#有
                组列表.append(' · '.join(速率列表))#速组
        if 用量 is not None:#有用量
            输出=用量['outputTokens'] if 'outputTokens' in 用量 and 用量['outputTokens'] is not None else 0#输出
            if 计费输入令牌(用量)>0 or 输出>0:#计费
                命中=缓存命中百分(用量)#命中
                if 命中 is not None:#有
                    组列表.append(翻译('stats.cacheHit',{'percent':命中}))#缓存
                组列表.append(翻译('stats.tokens',{'input':格式化令牌(计费输入令牌(用量),翻译),'output':格式化令牌(输出,翻译)}))#令牌
        if len(组列表)==0:#空
            return None#不画
        return {'type':'stats-line','groups':组列表,'line':' | '.join(组列表),'cssModule':'统计行.module.css'}#行

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

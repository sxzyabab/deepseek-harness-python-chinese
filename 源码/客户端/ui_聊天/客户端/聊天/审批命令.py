import json

__all__=['审批命令','命令自调用']


def 命令自调用(调用):
    '从关联工具调用的参数里取出 command。解析失败就没有'
    if not isinstance(调用,dict):
        return None
    原文=调用.get('argsRaw')
    if not isinstance(原文,str):
        return None
    try:
        参数=json.loads(原文)
    except json.JSONDecodeError:
        return None
    if isinstance(参数,dict) and isinstance(参数.get('command'),str):
        return 参数['command']
    return None


class 审批命令:
    '审批详情里显示关联工具调用的命令文本'
    def __init__(自身,属性=None):
        '记下审批标识和聊天选择器'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '找到 phase 为 start 且 callId 相同的根调用'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性.get('window')
        选=属性.get('useChat')
        命令=None
        if callable(选):
            def 挑选(快照):
                '遍历节点，只认还在 start 的根调用'
                节点表=快照.get('nodes') if isinstance(快照,dict) else None
                值表=节点表.values() if hasattr(节点表,'values') else []
                for 节点 in 值表:
                    if not isinstance(节点,dict) or 节点.get('kind')!='tool-call':
                        continue
                    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
                    根调用=数据.get('root')
                    if not isinstance(根调用,dict):
                        continue
                    if 根调用.get('callId')!=属性.get('callId'):
                        continue
                    if 'kind' in 根调用 or 根调用.get('phase')!='start':
                        continue
                    return 命令自调用(根调用)
                return None
            命令=选(挑选)
        if not isinstance(命令,str) or 窗口 is None:
            return None
        根=窗口.document.createElement('span')
        根.textContent=命令
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根

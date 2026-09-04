"""Client 目录键与公共 Runtime 脚本键之间的 realm 稳定翻译。"""
#对齐上游 worker/realms/client/scripts.ts

__all__=['Client脚本身份']#仅中文公开名

class Client脚本身份:#Client脚本身份
    """为一个 Client realm 内全部后端分配共享脚本身份命名空间。"""
    def __init__(自身,contextId):#构造
        """保存上下文 id 与本地映射。"""
        自身.contextId=contextId#上下文id
        自身._公开按本地={}#本地→公开

    def 转Runtime(自身,本地键):#转Runtime键
        """将 Client 本地键转换为该 realm 的公开 Runtime 脚本键。"""
        脚本键=自身._公开按本地.get(本地键)#已有
        if 脚本键 is not None:#复用
            return 脚本键#返回
        脚本键=f'client:{abs(自身.contextId)}:{len(自身._公开按本地)+1}'#合成键
        自身._公开按本地[本地键]=脚本键#登记
        return 脚本键#返回

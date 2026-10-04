from ...模型后端.llm.异常 import 装备错误

沙箱不可用码='SANDBOX_UNAVAILABLE'

class 沙箱不可用错误(装备错误):
    """隔离无法强制请求模式时抛出。
    经结构化错误通道携带 SANDBOX_UNAVAILABLE
    """
    def __init__(自身,模式,细节=None):
        """按模式与可选细节构造。
        面向用户的不可用说明不翻译字面量
        """
        消息=('sandbox mode "'+模式+'" is requested but no sandbox backend is usable on this host; '
            +'refusing to run the command unconfined. Install bubblewrap or run a Landlock-enforcing '
            +'kernel (Linux), ensure sandbox-exec is usable (macOS), or ensure the ACL '
            +'restricted-token runner can start (Windows) — otherwise switch the consumer to '
            +'danger-full-access.'
            +('' if 细节 is None else ' Runner failure: '+细节))
        装备错误.__init__(自身,消息,沙箱不可用码)

class 沙箱升级错误(Exception):
    '沙箱升级失败'

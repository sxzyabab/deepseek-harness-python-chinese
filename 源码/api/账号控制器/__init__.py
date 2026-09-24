from ...typert.协议 import 远程服务,远程 as _远程

__all__=['包名','名称','依赖','应用','默认','账号控制器']

包名='@deepseek-ai/dsh-api-account-controller'
名称='account-controller'
依赖=['deepseekAccount']

def _流方法(方法):
    """标为流式 Remote。"""
    方法._typert_remote_marker={'invocation':{'kind':'direct','mode':'stream'}}
    return 方法

class 账号控制器(远程服务):
    """账号 Remote 面，不携带凭证载荷。"""
    def __init__(自身,上下文):
        """登记 account 命名空间。"""
        super().__init__(上下文,'accountController',{'namespace':'account'})

    @_远程
    def getState(自身):
        """读安全账号投影。"""
        return 自身.ctx.deepseekAccount.获取状态()

    @_远程
    def getProfile(自身):
        """读展示用配置档；授予缺席或已更换时为 None。"""
        return 自身.ctx.deepseekAccount.获取配置档()

    @_远程
    def getBalance(自身):
        """读充值钱包余额；授予缺席或已更换时为 None。"""
        return 自身.ctx.deepseekAccount.获取平衡()

    @_远程
    def startSignIn(自身,区域,回调来源,登录来源):
        """开始浏览器登录。"""
        return 自身.ctx.deepseekAccount.开始登录(区域,回调来源,登录来源)

    @_远程
    def cancelSignIn(自身,尝试标识):
        """取消指定本地尝试。"""
        return 自身.ctx.deepseekAccount.取消登录(尝试标识)

    @_远程
    def signOut(自身):
        """去掉本地授予并在后台吊销，不删 API 密钥。"""
        return 自身.ctx.deepseekAccount.登出()

    @_流方法
    def watch(自身,信号):
        """推送安全账号投影。"""
        yield from 自身.ctx.deepseekAccount.监视(信号)

def 应用(上下文,配置值=None):
    """挂载账号 Remote 拥有者。"""
    账号控制器(上下文)

默认=应用
name=名称
inject=依赖
apply=应用
default=默认

from ...依赖.cordis import 服务

__all__=['包名','名称','依赖','应用','默认','合并平台Cookie','桌面客户端头','deepseek账号']

包名='@deepseek-ai/dsh-deepseek-account'
名称='deepseek-account'
依赖=[]

class deepseek账号(服务):
    """账号操作面；仅宿主可取请求凭证。"""
    def __init__(自身,上下文):
        """登记为 deepseekAccount。"""
        super().__init__(上下文,'deepseekAccount')

    def 获取状态(自身):
        """读已存账号与最近登录尝试，不含凭证。"""
        raise NotImplementedError('deepseekAccount.获取状态')

    def 获取配置档(自身):
        """独立查询配置档；已登出或授予已更换时为 None。"""
        raise NotImplementedError('deepseekAccount.获取配置档')

    def 获取平衡(自身):
        """独立查询钱包余额；已登出或授予已更换时为 None。"""
        raise NotImplementedError('deepseekAccount.获取平衡')

    def 开始登录(自身,区域,回调来源,登录来源):
        """加入在途尝试或启动浏览器授权，不等待批准。"""
        raise NotImplementedError('deepseekAccount.开始登录')

    def 取消登录(自身,标识):
        """只取消指定尝试；提交中的尝试先结算。"""
        raise NotImplementedError('deepseekAccount.取消登录')

    def 登出(自身):
        """去掉本地授予并后台吊销；远端失败不恢复授予。"""
        raise NotImplementedError('deepseekAccount.登出')

    def 监视(自身,信号):
        """含完整初值的快照流；结束订阅不取消登录。"""
        raise NotImplementedError('deepseekAccount.监视')

    def 解析令牌(自身,网址):
        """只给提供方允许的推理来源返回已存令牌。"""
        raise NotImplementedError('deepseekAccount.解析令牌')

    def 获取平台会话(自身):
        """读配置平台来源上的宿主凭证快照；已登出为 None。"""
        raise NotImplementedError('deepseekAccount.获取平台会话')

def 合并平台Cookie(基底,覆盖):
    """按区分大小写的名字合并 Cookie 对，覆盖方优先。"""
    表={}
    for 头 in (基底,覆盖):
        for 对 in 头.split(';'):
            分隔=对.find('=')
            if 分隔<1:
                continue
            表[对[0:分隔].strip()]=对[分隔+1:].strip()
    return '; '.join(名+'='+值 for 名,值 in 表.items())

def 桌面客户端头(平台):
    """识别原生桌面请求；None 表示非桌面，不改请求。"""
    if 平台 is None:
        return {}
    return {'x-client-platform':'desktop-win' if 平台=='win32' else 'desktop-mac'}

默认=deepseek账号
name=名称
inject=依赖
default=默认

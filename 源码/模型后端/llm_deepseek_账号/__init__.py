"""为 deepseek-account 注册账号令牌鉴权与模型发现。"""
from ..llm import (
    大模型错误,
    解析图片附件访问,
    重试政策错误,
    配额耗尽码,
)
from ...工具.启动环境 import 取启动环境
from ...身份.匿名用户id import 获取或创建匿名用户id
from ...配置.配置 import json深度相等
from ..llm_deepseek.适配器 import 深求适配器
from ..llm_deepseek.模型信息 import 目录模型信息
from .配置 import 配置,朴素选项,解析适配器选项,深求配置错误

__all__=(
    '名称','依赖','配置','应用','默认',
    '提供方','账号配额耗尽码','登录需求码','令牌无效码',
)

名称='llm-deepseek-account'
依赖=['llm']
提供方='deepseek-account'
账号配额耗尽码='ACCOUNT_QUOTA'
登录需求码='ACCOUNT_SIGN_IN_REQUIRED'
令牌无效码='ACCOUNT_TOKEN_INVALID'
提供方展示名='DeepSeek Account'

class 账号路由适配器(深求适配器):
    """账号路由：目录先鉴权；请求失败按账号语义改写。"""
    def __init__(自身,配置表,解析鉴权,处理请求错误):
        """挂上鉴权与失败改写钩子。"""
        super().__init__(配置表)
        自身.解析鉴权=解析鉴权
        自身.处理请求错误=处理请求错误
        自身.本请求令牌=None

    def 提供方简介(自身,提供方名):
        """展示名固定为账号路由。"""
        return {'id':提供方名,'name':提供方展示名}

    def 列出模型(自身,提供方名):
        """未登录或目标不允许账号鉴权时目录为空。"""
        连接=自身.配置['选项']()
        try:
            自身.解析鉴权(连接)
        except 大模型错误 as 错误:
            if 错误.code==登录需求码:
                return []
            raise
        return [目录模型信息(提供方名,模型) for 模型 in 连接['models']]

    def 请求(自身,选项,连接,信号,活动):
        """先锁定本请求令牌，离开前改写可识别的账号失败。"""
        自身.本请求令牌=自身.解析鉴权(连接)
        try:
            try:
                yield from super().请求(选项,连接,信号,活动)
            except Exception as 错误:
                raise 自身.处理请求错误(错误,自身.本请求令牌)
        finally:
            自身.本请求令牌=None

def 从失败拆选项(失败快照,原因):
    """把冻结的 failure 快照收成大模型错误构造选项。"""
    选项={'cause':原因}
    if 'status' in 失败快照:
        选项['status']=失败快照['status']
    if 'providerRetryAfterMs' in 失败快照:
        选项['providerRetryAfterMs']=失败快照['providerRetryAfterMs']
    if 'requestId' in 失败快照:
        选项['requestId']=失败快照['requestId']
    if 'offloadImages' in 失败快照:
        选项['offloadImages']=失败快照['offloadImages']
    return 选项

def 应用(上下文,原始配置=None):
    """加载插件：账号令牌鉴权，不回退到 API 密钥。"""
    if 原始配置 is None:
        原始配置={}
    def 关闭设置自动(子):
        """本纤程关闭 settings 自动写入。"""
        def 挂配置():
            """把 auto:false 绑到本插件纤程。"""
            return 子.settings.configure({'auto':False},上下文.纤程)
        子.副作用(挂配置)
    上下文.依赖启动(['settings'],关闭设置自动)
    def 选项():
        """按请求解析连接事实。"""
        return 解析适配器选项(朴素选项(原始配置),取启动环境(上下文))
    选项()
    def 解析鉴权(连接):
        """解析账号令牌；缺席则报登录需求。"""
        账号=上下文.获取服务('deepseekAccount')
        令牌=None
        if 账号 is not None:
            令牌=账号.解析令牌(连接['baseURL'])
        if 令牌 is None:
            raise 大模型错误(
                '请登录 DeepSeek 以使用账号提供方。请求目标必须允许账号鉴权。',
                登录需求码,
            )
        return 令牌
    def 解析账号令牌(连接):
        """适配器钩子：优先本请求已锁定的令牌。"""
        if 适配器.本请求令牌 is not None:
            return 适配器.本请求令牌
        return 解析鉴权(连接)
    def 处理请求错误(错误,令牌):
        """QUOTA→ACCOUNT_QUOTA；HTTP 401→令牌无效并尝试清除匹配凭据。"""
        if not isinstance(错误,大模型错误):
            return 错误
        if 错误.code==配额耗尽码:
            return 大模型错误(错误.message,账号配额耗尽码,从失败拆选项(错误.failure,错误))
        if 'status' not in 错误.failure or 错误.failure['status']!=401:
            return 错误
        已拒绝=大模型错误(错误.message,令牌无效码,从失败拆选项(错误.failure,错误))
        账号=上下文.获取服务('deepseekAccount')
        if 账号 is not None:
            try:
                账号.拒绝令牌(令牌)
            except Exception:
                #存储清除失败不能替代推理失败本身
                pass
        return 已拒绝
    用户标识=None
    def 解析用户标识():
        """首次签发后复用。"""
        nonlocal 用户标识
        if 用户标识 is None:
            用户标识=获取或创建匿名用户id()
        return 用户标识
    def 解析附件():
        """当前附件仓；缺席对纯文本合法。"""
        return 上下文.获取服务('attachments')
    def 解析图片访问(附件仓,引用):
        """把附件仓上的宿主路径桥进已挂载的工具执行世界。"""
        文件系统=上下文.获取服务('fs')
        def 映射宿主路径(宿主路径):
            """宿主对象位置到进程路径。"""
            if 文件系统 is None:
                return None
            return 文件系统.从宿主路径映射进程路径(宿主路径)
        return 解析图片附件访问(附件仓,映射宿主路径,引用)
    def 准备扩展(请求):
        """准备插件贡献字段。"""
        扩展=上下文.获取服务('deepseekLlmApiExtensions')
        if 扩展 is None:
            def 接纳():
                """无贡献。"""
                return None
            return {'fields':{},'accept':接纳}
        return 扩展.准备(请求)
    def 回放降级(细节):
        """报告不可用消息回放，不暴露耐久内容或签名。"""
        上下文.日志.警告('llm-deepseek: unusable Messages replay state on assistant history for route "'+str(细节['provider'])+'/'+str(细节['model'])+'"; sending provider-neutral content ('+str(细节['reason'])+')')
    适配器=账号路由适配器({
        '选项':选项,
        '解析账号令牌':解析账号令牌,
        '解析用户标识':解析用户标识,
        '解析附件':解析附件,
        '解析图片访问':解析图片访问,
        '准备扩展':准备扩展,
        '回放降级':回放降级,
    },解析鉴权,处理请求错误)
    入口=上下文.纤程.插件配置
    设置命名=名称
    if 入口 is not None:
        设置命名=入口.选项['id']
    上下文.llm.注册可配置提供方([
        {'provider':提供方,'displayName':提供方展示名,'settingsNs':设置命名,'settingsPath':[]},
    ])
    登记=上下文.llm.注册适配器([提供方],适配器)
    已登记政策=选项()['retryPolicy']
    def 确保登记事实():
        """政策变了则就地替换。"""
        nonlocal 已登记政策
        try:
            政策=选项()['retryPolicy']
        except (深求配置错误,重试政策错误) as 错误:
            上下文.日志.警告(错误)
            return
        if json深度相等(政策,已登记政策):
            return
        登记.替换([提供方])
        已登记政策=政策
    上下文.监听('loader/volatile-update',确保登记事实)

默认=应用
name=名称
inject=依赖
apply=应用
Config=配置
default=应用

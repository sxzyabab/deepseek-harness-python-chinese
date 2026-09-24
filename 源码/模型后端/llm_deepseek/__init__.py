"""向 llm 注册 deepseek-official 提供方适配器。"""
from ..llm import (
    断言可用接口密钥,
    大模型错误,
    解析图片附件访问,
    重试政策错误,
)
from ...工具.启动环境 import 取启动环境
from ...身份.匿名用户id import 获取或创建匿名用户id
from ...配置.配置 import json深度相等
from .配置 import 配置,公开基址,消息基址,解析适配器选项,深求配置错误,朴素选项
from .默认值 import (
    默认上下文窗口,
    默认文件过期秒,
    默认文件配额清理批,
    默认文件刷新边距秒,
    默认文件接口超时毫秒,
    默认图片卸载字节量子,
    默认图片卸载张数量子,
    默认内联图片卸载字节量子,
    默认最大内联请求图字节,
    默认最大令牌,
    默认流空闲超时毫秒,
)
from .适配器 import 深求适配器
from .请求定价 import (
    默认低细节图像素预算,
    默认每请求最大图片数,
    默认最大请求文件字节,
    默认请求图最大字节,
    请求图最大边,
    深求图片请求定价,
    解析请求图最大字节,
    解析请求图目标,
)
from .图片令牌 import 深求图片令牌,深求请求图尺寸
from .文件仓 import 深求文件仓,最大图片字节
from .文件接口 import (
    深求文件客户端,
    最小文件过期秒,
    最大文件过期秒,
    最大文件上传字节,
    最大存储文件数,
    最大存储文件字节,
)
from .上传索引 import 深求上传索引,深求文件作用域摘要
from .文件标识 import 深求文件标识

__all__=(
    '名称','依赖','配置','应用','默认',
    '设置空间','公开基址','消息基址','解析适配器选项','深求配置错误','朴素选项',
    '默认上下文窗口','默认文件过期秒','默认文件配额清理批','默认文件刷新边距秒',
    '默认文件接口超时毫秒','默认图片卸载字节量子','默认图片卸载张数量子',
    '默认内联图片卸载字节量子','默认最大内联请求图字节','默认最大令牌','默认流空闲超时毫秒',
    '深求适配器',
    '默认低细节图像素预算','默认每请求最大图片数','默认最大请求文件字节',
    '默认请求图最大字节','请求图最大边','深求图片请求定价','解析请求图最大字节','解析请求图目标',
    '深求图片令牌','深求请求图尺寸','深求文件标识',
    '深求文件仓','最大图片字节','深求文件客户端',
    '最小文件过期秒','最大文件过期秒','最大文件上传字节',
    '最大存储文件数','最大存储文件字节','深求上传索引','深求文件作用域摘要',
)

名称='llm-deepseek'
依赖=['llm']
设置空间='llm-deepseek'
提供方='deepseek-official'

def 应用(上下文,原始配置=None):
    """加载插件：按请求解析连接事实并注册路由。"""
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
    def 解析接口密钥(连接):
        """按快照解析密钥。"""
        引用=连接['apiKeyEnv']
        凭证=上下文.获取服务('credentials')
        if 凭证 is not None:
            命中=凭证.解析(引用)
            if 命中 is not None:
                return 断言可用接口密钥(命中['value'],'llm-deepseek',引用)
        else:
            环境项=取启动环境(上下文).取(引用)
            if 环境项 is not None and len(环境项['value'])>0:
                return 断言可用接口密钥(环境项['value'],'llm-deepseek',引用)
        缺密钥文案='llm-deepseek: no API key for provider route "'+提供方+'"; store '+str(引用)+' through the credentials service (the web Models page writes it), or export '+str(引用)+' in the launching environment'
        raise 大模型错误(缺密钥文案,'MISSING_CREDENTIAL')
    def 解析账号令牌(连接):
        """仅官方端点解析账号令牌。"""
        账号=上下文.获取服务('deepseekAccount')
        if 账号 is None:
            return None
        return 账号.解析令牌(连接['baseURL'])
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
    适配器=深求适配器({
        '选项':选项,
        '解析接口密钥':解析接口密钥,
        '解析账号令牌':解析账号令牌,
        '解析用户标识':解析用户标识,
        '解析附件':解析附件,
        '解析图片访问':解析图片访问,
        '准备扩展':准备扩展,
        '回放降级':回放降级,
    })
    入口=上下文.纤程.插件配置
    设置命名=设置空间
    if 入口 is not None:
        设置命名=入口.选项['id']
    上下文.llm.注册可配置提供方([
        {'provider':提供方,'displayName':'DeepSeek','settingsNs':设置命名,'settingsPath':[]},
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

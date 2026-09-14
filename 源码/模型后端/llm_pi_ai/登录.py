import pi_ai#外部依赖胶水
from ...凭据.凭据 import 是否凭证键段#键段判定
from .目录 import 目录提供方,目录提供方标识列表#目录
from .认证 import 记录键于#记录键

__all__=['登记派爱登录流']#仅中文公开名

def 登录方法(提供方):
    """一个目录提供方提供的登录方法；最偏好在前。"""
    方法列表=[]#方法
    if 提供方 is None:#无
        return 方法列表#空
    认证=getattr(提供方,'auth',None)#认证块
    if 认证 is None:#无
        return 方法列表#空
    oauth=getattr(认证,'oauth',None)#oauth
    if oauth is not None:#有 oauth
        标签=getattr(oauth,'loginLabel',None) or getattr(oauth,'name',None) or 'OAuth'#标签
        方法列表.append({'id':'oauth','label':标签})#oauth
    api键=getattr(认证,'apiKey',None)#api-key
    if api键 is not None and getattr(api键,'login',None) is not None:#有交互登录
        方法列表.append({'id':'api-key','label':getattr(api键,'name',None) or 'API Key'})#密钥
    return 方法列表#方法

def 中继(事件,会话):
    """用 seam 词表重述一次 pi-ai 登录事件。"""
    类型=getattr(事件,'type',None) or (事件.get('type') if isinstance(事件,dict) else None)#类型
    def 取(名,默认=None):
        """属性或键。"""
        if isinstance(事件,dict):#dict
            return 事件[名] if 名 in 事件 else 默认#键
        return getattr(事件,名,默认)#属性
    if 类型=='info':#信息
        链接列表=取('links') or []#链接
        链=链接列表[0] if len(链接列表)>0 else None#首链
        通知={'message':取('message')}#消息
        if 链 is not None:#有链
            地址=链['url'] if isinstance(链,dict) else getattr(链,'url',None)#url
            if 地址 is not None:#有
                通知['url']=地址#url
        会话['notify'](通知)#通知
        return#结束
    if 类型=='auth_url':#授权 URL
        会话['notify']({
            'message':取('instructions') or '打开此页面以继续登录。',
            'url':取('url'),
        })#通知
        return#结束
    if 类型=='device_code':#设备码
        会话['notify']({
            'message':'在验证页输入此代码以完成登录。',
            'url':取('verificationUri'),
            'code':取('userCode'),
        })#通知
        return#结束
    if 类型=='progress':#进度
        会话['notify']({'message':取('message')})#通知
        return#结束
    会话['notify']({'message':'正在登录…'})#未知成员仍显示有事在发生

def 重述(提示):
    """用 seam 词表重述一次 pi-ai 提示。"""
    def 取(名,默认=None):
        """属性或键。"""
        if isinstance(提示,dict):#dict
            return 提示[名] if 名 in 提示 else 默认#键
        return getattr(提示,名,默认)#属性
    信号=取('signal')#信号
    信号块={} if 信号 is None else {'signal':信号}#可选信号
    类型=取('type')#类型
    if 类型=='select':#选择
        return {**信号块,'kind':'select','message':取('message'),'options':取('options')}#选择
    if 类型=='secret':#密钥
        结果={**信号块,'kind':'secret','message':取('message')}#密钥
        占位=取('placeholder')#占位
        if 占位 is not None:#有
            结果['placeholder']=占位#占位
        return 结果#提示
    结果={**信号块,'kind':'text','message':取('message')}#文本
    占位=取('placeholder')#占位
    if 占位 is not None:#有
        结果['placeholder']=占位#占位
    return 结果#提示

def 登记派爱登录流(上下文,认证注入):
    """为每个自带登录的已安装提供方登记一条授权流。"""
    for 提供方标识 in 目录提供方标识列表():#逐目录
        提供方=目录提供方(提供方标识)#提供方
        方法列表=登录方法(提供方)#方法
        if 提供方 is None or len(方法列表)==0:#无登录
            continue#跳过
        if not 是否凭证键段(提供方标识):#非法段
            上下文.日志.警告(
                'llm-pi-ai: catalog provider "%s" cannot address a credential record; its sign-in is not offered',
                提供方标识,
            )#警告
            continue#跳过
        def 执行登录(会话,标识=提供方标识,方=提供方):
            """一次登录尝试。会话为 dict。"""
            模型集合=pi_ai.createModels(认证注入)#自有集合
            模型集合.setProvider(方)#挂提供方
            类型='oauth' if 会话.get('method')=='oauth' else 'api_key'#认证类型
            def 通知(事件):
                """中继。"""
                中继(事件,会话)#中继
            def 提问(提示):
                """重述后提问。"""
                return 会话['prompt'](重述(提示))#提示
            模型集合.login(标识,类型,{
                'signal':会话.get('signal'),
                'notify':通知,
                'prompt':提问,
            })#登录
        上下文.authorization.注册流程({
            'key':记录键于(提供方标识),
            'label':getattr(提供方,'name',提供方标识),
            'methods':方法列表,
            'run':执行登录,
        })#登记

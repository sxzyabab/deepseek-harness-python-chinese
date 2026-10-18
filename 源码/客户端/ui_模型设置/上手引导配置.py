'宿主和浏览器共用的页面引导选项'

__all__=['配置','上手引导配置全局键','Config']

上手引导配置全局键='__DSH_MODELS_ONBOARDING__'

def 配置(原始=None):
    '校验页面引导选项。缺省开启凭据引导'
    if 原始 is None:
        原始={}
    if isinstance(原始,dict) is False:
        raise Exception('onboarding config must be an object')
    if 'credentialOnboarding' in 原始:
        开关=原始['credentialOnboarding']
        if isinstance(开关,bool) is False:
            raise Exception('credentialOnboarding must be a boolean')
    else:
        开关=True
    return {'credentialOnboarding':开关}

Config=配置

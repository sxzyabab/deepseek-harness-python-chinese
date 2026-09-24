__all__=['浏览器页选项','浏览器页']

def 浏览器页选项(初始,持久,打开请求):
    """构造导航提供方输入；持久化不进入活动导航接口。"""
    return {'initial':初始,'persist':持久,'openRequested':打开请求}

def 浏览器页(帧,呈现形式):
    """导航提供方与呈现形式的组合。"""
    return {'frame':帧,'presentation':呈现形式}

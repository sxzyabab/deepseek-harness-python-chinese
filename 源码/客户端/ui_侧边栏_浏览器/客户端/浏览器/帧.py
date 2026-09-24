__all__=['空浏览器帧']

def 空浏览器帧():
    """尚无页面目标时的导航态。"""
    return {
        'target':None,
        'address':'empty',
        'loading':False,
        'canGoBack':False,
        'canGoForward':False,
        'error':None,
        'sandboxEnabled':None,
    }

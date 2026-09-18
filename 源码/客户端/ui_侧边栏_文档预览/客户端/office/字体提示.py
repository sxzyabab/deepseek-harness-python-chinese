"""缺字体提示与非模态详情面板，绑定同一源版本。"""

__all__=['字体提示']#仅中文公开名

def 字体提示(属性):
    """展示缺字体；关闭仅对本源版本在本组件仍挂载期间生效。"""
    字体=属性.get('fonts') or []#缺字体列表
    if len(字体)==0:#齐备
        return None#无
    翻译=属性['t']#翻译
    return {#提示结构
        'kind':'font-notice',
        'message':翻译('missingFonts',{'fonts':', '.join(字体)}),
        'title':翻译('missingFontsTitle'),
        'description':翻译('missingFontsDescription'),
        'count':翻译('missingFontsCount',{'count':len(字体)}),
        'fonts':list(字体),
        'showMore':翻译('showMore'),
        'dismiss':翻译('dismissNotice'),
        'closeDetails':翻译('closeDetails'),
    }#结束

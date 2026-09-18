__all__=['插件面板图标']#仅中文公开名

def 插件面板图标(属性):
    """侧栏插件入口图标；按钮、标签与选中态由侧栏拥有。"""
    尺寸=属性['size'] if 'size' in 属性 else 16#边长
    return {'kind':'icon','name':'IconPluginPinwheelOutline16','size':尺寸}#结构

__all__=['点外关闭']

def 点外关闭(根,打开,置关,传送=None):
    '表面开着时，点在根和传送层外面就调用置关(False)。返回拆除函数'
    if 打开 is not True or 根 is None:
        return lambda: None
    文档=根.ownerDocument
    def 在内(盒,目标):
        '盒存在且包住目标'
        if 盒 is None:
            return False
        return 盒.contains(目标) is True
    def 关闭(事件):
        '根和传送层都不包含目标时关掉'
        目标=事件.target
        if 在内(根,目标):
            return
        if 在内(传送,目标):
            return
        置关(False)
    文档.addEventListener('pointerdown',关闭)
    def 拆除():
        '卸掉这次的 pointerdown'
        文档.removeEventListener('pointerdown',关闭)
    return 拆除

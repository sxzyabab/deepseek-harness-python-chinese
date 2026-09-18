"""已加载 Office 预览在正文重挂后仍存活，直到重载或标签关闭。"""

__all__=['创建Office存储']#仅中文公开名

def 创建Office存储():
    """在会话内跨正文重挂保留 Office 内容。"""
    状态={'byTab':{}}#按标签
    def 加载中(标签,修订):
        """标加载中。"""
        状态['byTab'][标签]={'revision':修订}#写入
    def 完成(标签,修订,文件):
        """写入成功文件。"""
        状态['byTab'][标签]={'revision':修订,'file':文件}#完成
    def 失败(标签,修订,失败信息):
        """写入失败。"""
        状态['byTab'][标签]={'revision':修订,'failure':失败信息}#失败
    def 忘记(标签):
        """去掉已关标签。"""
        if 标签 in 状态['byTab']:#有
            del 状态['byTab'][标签]#删
    return {'state':状态,'actions':{'loading':加载中,'complete':完成,'failed':失败,'forget':忘记}}#句柄

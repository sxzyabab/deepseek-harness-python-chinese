"""独立的内容到终端记录，使并发浏览器写入互不干扰。"""
import json#持久
import re#身份形态

__all__=['终端绑定']#仅中文公开名

前缀='dsh.terminal.binding.v1.'#存储前缀
身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端 id

class 终端绑定:
    """按会话与内容身份键控的已保存恢复目标。"""

    def __init__(自身,本地存储=None):
        """可选依赖 localStorage 面。"""
        自身._内存={}#内存表
        自身._存储=本地存储#存储

    def 获取(自身,会话标识,内容标识):
        """读取已保存目标。"""
        键=自身._键(会话标识,内容标识)#键
        if 键 in 自身._内存:#内存
            return 自身._内存[键]#命中
        if 自身._存储 is None:#无存储
            return None#无
        try:
            原始=自身._存储.getItem(键)#读
            if 原始 is None:#无
                return None#无
            值=json.loads(原始)
            if not isinstance(值,str) or 身份形态.match(值) is None:#非法
                return None#无
            自身._内存[键]=值#缓存
            return 值
        except (TypeError,ValueError,AttributeError):
            return None

    def 设置(自身,会话标识,内容标识,终端标识):
        """在 Host 分配开始前保存身份。"""
        键=自身._键(会话标识,内容标识)#键
        自身._内存[键]=终端标识#内存
        if 自身._存储 is None:#无存储
            return
        try:
            自身._存储.setItem(键,json.dumps(终端标识,ensure_ascii=False,separators=(',',':')))#持久
        except (TypeError,ValueError,AttributeError) as 错误:
            print('Terminal binding persistence failed:',错误)

    def 删除(自身,会话标识,内容标识):
        """关闭意图已保存后移除本内容目标。"""
        键=自身._键(会话标识,内容标识)#键
        自身._内存.pop(键,None)#内存
        if 自身._存储 is None:#无存储
            return
        try:
            自身._存储.removeItem(键)#持久
        except (TypeError,ValueError,AttributeError) as 错误:
            print('Terminal binding cleanup failed:',错误)

    def 清空(自身):
        """Client 服务拆除时释放缓存。"""
        自身._内存.clear()#清空

    def _键(自身,会话标识,内容标识):
        """存储键。"""
        return 前缀+json.dumps([会话标识,内容标识],ensure_ascii=False,separators=(',',':'))#键

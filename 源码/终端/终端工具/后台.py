"""后台终端发送对通用任务拉取源的适配。"""
from .渲染 import 渲染发送读取

def 发送源(操作):
    """把后端的消费型发送读取器适配成注册表拉取源。操作是零参可调用，返回活发送或 None。"""
    def 读取(起始字节):
        """按已交付字节保持游标单调；发送尚未开始则交空。"""
        活=操作()
        if 活 is None:
            return {'text':'','nextOffset':起始字节,'lossy':False}
        文本=渲染发送读取(活.读取输出())
        return {'text':文本,'nextOffset':起始字节+len(文本.encode('utf-8')),'lossy':False}
    return {'read':读取}

__all__=['发送源']

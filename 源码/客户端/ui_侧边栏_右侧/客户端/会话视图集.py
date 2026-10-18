'选中的会话和还要留着的后台视图'
from ...存储 import 创建快照存储
from ..异常 import 右侧侧栏错误
from .会话视图 import 侧栏会话视图

__all__=['侧栏会话视图集']


class 侧栏会话视图集:
    '前台会话和还留着正文的后台视图。插件关掉时全部释放'

    def __init__(自身,会话面):
        '先是空名单'
        自身.会话面=会话面
        自身.源=创建快照存储(())
        自身.视图={}
        自身.按引用={}
        自身.已选=None
        自身.已关=False

    def 选择(自身,会话标识):
        '换前台。后台里还有正文的视图先留着'
        if 自身.已关 or 自身.已选==会话标识:
            return
        自身.已选=会话标识
        if 会话标识 is not None and 会话标识 not in 自身.视图:
            def 拆除时(已拆):
                '从引用索引摘掉'
                if 已拆.引用 in 自身.按引用:
                    del 自身.按引用[已拆.引用]

            def 标签释放时(已放):
                '正文松手后再看要不要退役'
                自身._修剪(已放)

            视图=侧栏会话视图(会话标识,自身.会话面,拆除时,标签释放时)
            自身.视图[会话标识]=视图
            自身.按引用[视图.引用]=视图
        for 视图 in list(自身.视图.values()):
            自身._修剪(视图)
        自身._发布()

    def 挂载(自身,引用):
        '绑定一棵已经提交的根'
        视图=自身.按引用.get(引用)
        if 视图 is None:
            if 自身.已关:
                def 空卸():
                    '插件已经关了'
                    return None
                return 空卸
            raise 右侧侧栏错误('Sidebar Session view reference is no longer owned')
        return 视图.挂载()

    def 拆除(自身):
        '全部释放，不等页面卸载'
        自身.已关=True
        自身.视图.clear()
        自身.源.set(())
        for 视图 in list(自身.按引用.values()):
            视图.拆除()

    def _修剪(自身,视图):
        '不是前台、也没有保留正文，就撤出'
        if 视图.会话标识==自身.已选 or 视图.有保留标签 or 自身.视图.get(视图.会话标识) is not 视图:
            return
        del 自身.视图[视图.会话标识]
        自身._发布()
        视图.退役()

    def _发布(自身):
        '按会话标识排序后交给根'
        表=list(自身.视图.values())
        表.sort(key=lambda 视图: 视图.会话标识)
        行=[]
        for 视图 in 表:
            行.append({
                'sessionId':视图.会话标识,
                'reference':视图.引用,
                'selected':视图.会话标识==自身.已选,
                'retainTab':视图.保留标签,
            })
        自身.源.set(tuple(行))

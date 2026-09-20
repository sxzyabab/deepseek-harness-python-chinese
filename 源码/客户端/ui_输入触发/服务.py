from ...依赖 import cordis#外部依赖胶水
from ...工具.值 import 带值弱映射#按座位绑定弱缓存控制器
服务=cordis.服务#Cordis 服务基类
from .控制器 import 触发控制器,触发错误#每会话控制器与本包异常

__all__=['触发服务']#仅中文公开名

class 触发服务(服务):#ctx.inputTriggers 触发管线
    """根登记表 + 按会话绑定弱映射的控制器解析。"""
    def __init__(自身,上下文):#挂到 inputTriggers
        """初始化源表与每会话控制器弱表。"""
        super().__init__(上下文,'inputTriggers')#以 inputTriggers 登记
        自身.源列表=[]#已登记的触发源
        自身.控制器表=带值弱映射()#按座位绑定弱缓存控制器
        上下文.on('locale/change',自身._文案变更)#文案切换时刷新开放菜单

    def _文案变更(自身):#locale/change
        """重拉每个会话的开放菜单候选。"""
        for 控 in 自身.控制器表.values:#每个已活会话
            控.refreshOpenMenu()#重拉候选

    def registerSource(自身,源):#登记一个触发源
        """trigger+name 必须唯一——重复则抛；返回拆除器。"""
        触发=源['trigger']#触发字符
        名=源['name']#源名
        for 已 in 自身.源列表:#查重
            if 已['trigger']==触发 and 已['name']==名:#重复
                raise 触发错误('斜杠源 "'+str(触发)+str(名)+'" 已经登记')#抛
        自身.源列表.append(源)#写入花名册
        for 控 in 自身.控制器表.values:#通知每个已活会话
            try:#晚到源仍须预热并入词库
                控.sourceAdded(源)#通知该会话源已加入
            except Exception as 错误:#源回调故障；源回调异常契约未定，故不能换成更窄的 except
                print('[ui-input-trigger] 源 "'+str(触发)+str(名)+'" 迟登记安装失败:',错误)#记错误
        def 拆除源():#拆除该源
            """从花名册摘掉并通知控制器。"""
            if 源 not in 自身.源列表:#已拆除则幂等
                return#返回
            自身.源列表.remove(源)#摘掉
            for 控 in 自身.控制器表.values:#通知各会话
                控.sourceRemoved(源)#拆除通知
        return 拆除源#拆除器

    def sessionOf(自身,作用域):#按会话取触发控制器
        """惰性；绑定作用域拆除器会移除并拆除它。"""
        会话面=自身.ctx.获取服务('sessions')#会话面
        if 会话面 is None:#未挂载
            raise 触发错误('ui-input-trigger: sessions 服务不可用')#抛
        会话=会话面.sessionOf(作用域)#会话代际
        绑定=None if 会话 is None else 会话面.binding(会话.sessionId)#座位绑定
        if 绑定 is None or 绑定.session is not 会话:#必须保留代际
            raise 触发错误('slash.sessionOf requires a retained Session scope')#抛
        标识=绑定.sessionId#会话身份
        键=绑定.ctx#弱键用绑定上下文
        已有=自身.控制器表.get(键)#已有则复用
        if 已有 is not None:#命中
            return 已有#复用
        def 按触发(触发字符):#过滤排序
            """登记顺序保留，order 越小越前。"""
            出=[s for s in 自身.源列表 if s['trigger']==触发字符]#同触发
            def 源顺序(源项):#order 键
                """缺席当 0。"""
                return 源项['order'] if 'order' in 源项 and 源项['order'] is not None else 0#顺序
            出.sort(key=源顺序)#按 order
            return 出#列表
        def 全部源():#名册全量
            """登记顺序副本。"""
            return list(自身.源列表)#列表
        控=触发控制器({'actx':绑定.ctx,'sessionId':标识,'roster':{'sources':按触发,'all':全部源}})#本会话触发控制器
        自身.控制器表.set(键,控)#记入弱表
        def 拆除会话控制器():#绑定作用域拆除时清控制器
            """dispose 并删表。"""
            def 清():#清
                """拆除。"""
                控.dispose()#拆除控制器
                自身.控制器表.delete(键)#从表删除
            return 清#拆除器
        绑定.ctx.副作用(拆除会话控制器,'slash: session controller')#登记
        return 控#新常驻控制器

依赖=['sessions']
inject=依赖#框架槽
触发服务.inject=依赖#框架槽

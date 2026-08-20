"""组进每个可续跑子体未发布创建上下文的部署能力的内部注册表。一项贡献授予子作用域能力，而不教续跑管理器存在哪些能力。"""
from llm import 错误链#errorChain 渲染
from .错误 import 子智能体错误#导入子智能体错误

def 是否已移除(登记):#是否已撤销
    """贡献可能已自行撤销后重读可变移除状态。"""
    return 登记['removed']#可变字段

# ContinuableSetupContribution：(childCtx) -> disposer；同步子作用域安装器。
可续跑装配贡献=object#类型占位（调用约定：(子上下文)->拆除器）

class 子智能体激活装配注册表:#装配注册表
    """拥有可续跑子体装配登记、安装、回滚、子清理与立即活撤销。"""
    def __init__(自身):#空注册表
        """空注册表。"""
        自身._登记们=[]#按安装顺序的活贡献
        自身._按子={}#子上下文到其活安装列表

    def 登记(自身,贡献):#登记贡献
        """登记一项贡献。返回幂等的登记撤销。尝试每个安装后若任何 disposer 失败则抛。"""
        登记={'contribution':贡献,'removed':False,'installations':[]}#新建登记
        自身._登记们.append(登记)#写入活集
        def 撤销():#撤销登记
            """幂等的登记撤销。"""
            if 登记['removed']:#已撤销
                return#幂等
            # 拆除之前关闭，使已快照的 apply() 不能在撤销报告完成后安装。
            登记['removed']=True#关闭准入
            if 登记 in 自身._登记们:#仍在活集
                自身._登记们.remove(登记)#移出活集
            自身._全部释放(list(登记['installations']),'contribution removal')#释放全部安装
        return 撤销#撤销器

    def 应用(自身,子上下文):#安装全部活贡献
        """把每个活贡献安装进一个未发布子上下文。返回 Agent 发布时消费的供应提交。"""
        状态={'installations':[],'invalidated':False}#本批事务
        try:#安装可能抛
            for 登记 in list(自身._登记们):#快照后逐项
                if 登记['removed']:#快照后已撤销则跳过
                    continue#跳过
                拆除器=登记['contribution'](子上下文)#同步安装
                安装={'registration':登记,'childCtx':子上下文,'dispose':拆除器,'released':False,'transaction':状态}#一次安装记录
                登记['installations'].append(安装)#记入登记
                状态['installations'].append(安装)#记入本批
                索引=自身._按子.get(子上下文)#该子的安装集
                if 索引 is None:#尚无索引
                    索引=[]#新建
                    自身._按子[子上下文]=索引#挂上
                索引.append(安装)#记入按子索引
                # 安装器可能在其安装记录存在之前自行撤销。释放那条逃逸记录并使供应批次作废。
                if 是否已移除(登记):#安装中途撤销
                    自身._释放(安装)#释放
        except Exception as 错误:#安装器失败
            # 保持安装器失败为权威，但尝试每一次回滚。
            try:#回滚不得掩盖原失败
                自身._全部释放(list(状态['installations']),'setup rollback')#回滚本批
            except Exception:#回滚也失败
                pass#吞掉回滚失败
            raise 错误#原安装失败
        def 子拆除工厂():#子作用域拆除时释放
            """返回子作用域拆除时释放安装的 disposer。"""
            def 子拆除():#子作用域拆除时释放
                """子作用域拆除时释放。"""
                自身._释放子(子上下文)#释放一子
            return 子拆除#拆除器
        子上下文.effect(子拆除工厂,'subagents.activationSetup()')#子作用域拆除时释放
        def 提交():#发布边界提交
            """发布边界提交。"""
            if 状态['invalidated']:#供应期间被撤销
                raise 子智能体错误(#拒绝建立
                    'a continuable-subagent setup contribution was revoked while this child was being built; '#文案前
                    +'the child was not established',#文案后
                    'ACTIVATION_SETUP_REVOKED',#错误码
                )#SubagentError结束
            for 安装 in 状态['installations']:#驻留后摘掉事务
                安装['transaction']=None#摘掉
        return {'commit':提交}#供应提交

    def _释放子(自身,子上下文):#释放一子
        """释放一个已拆除子作用域拥有的每个剩余安装。"""
        索引=自身._按子.get(子上下文) or []#该子安装
        自身._全部释放(list(索引),'child scope disposal')#全部释放

    def _全部释放(自身,安装们,期间):#释放一批
        """在报告 disposer 失败之前完整释放一批。"""
        失败们=[]#释放失败
        for 安装 in 安装们:#逐条
            try:#隔离单条失败
                自身._释放(安装)#释放一条
            except Exception as 错误:#disposer抛
                失败们.append(错误)#记下
        if len(失败们)==0:#全部成功
            return#成功
        raise 子智能体错误(#聚合失败
            'continuable-subagent setup '+期间+' failed to release '+str(len(失败们))+' installation(s): '#文案前
            +'; '.join([错误链(失败) for 失败 in 失败们]),#文案后
            'ACTIVATION_SETUP_RELEASE_FAILED',#错误码
        )#SubagentError结束

    def _释放(自身,安装):#释放一条
        """从两个索引丢掉一次安装并恰好拆除它一次。"""
        if 安装.get('released'):#幂等
            return#已释放
        安装['released']=True#先标记
        登记=安装['registration']#所属登记
        安装集=登记['installations']#登记列表
        if 安装 in 安装集:#仍在
            安装集.remove(安装)#移出登记
        索引=自身._按子.get(安装['childCtx'])#按子索引
        if 索引 is not None:#有索引
            if 安装 in 索引:#仍在
                索引.remove(安装)#移出
            if len(索引)==0:#空则摘掉子键
                自身._按子.pop(安装['childCtx'],None)#摘掉
        if 安装.get('transaction') is not None:#有供应批
            安装['transaction']['invalidated']=True#作废供应批
        安装['dispose']()#调用安装disposer

默认=子智能体激活装配注册表#默认导出

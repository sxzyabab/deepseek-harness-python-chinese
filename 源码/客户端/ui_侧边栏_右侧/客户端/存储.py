"""停靠表面存储：每会话一份布局，纯规划器算、存储只整表写回。

对齐上游 `ui-sidebar-right/src/client/stores.ts`。公开面仅中文名。
产品规则：展开列不停靠空窗；折叠列可空；页面种类每窗至多一枚。跨包值为 dict。
句柄自持订阅；规格形同 defineStore（init/actions/create）。
"""
from ...ui_停靠套件.引擎 import (#停靠引擎（避开组件包导入）
    创建初始状态,
    空历史,
    记录,
    回放,
    后退一步,
    前进一步,
    活动停靠窗格标识,
    停靠窗格标识列表,
    查找标签窗格,
    查找窗格内容标签,
    取窗格,
    规划打开内容,
    规划落定,
    规划设展开,
    规划设模式,
    规划分窗格,
    规划复制标签,
    规划安置标签,
    规划投放标签,
    规划浮出标签,
    规划收回浮窗,
    规划调整分割,
)#引擎结束
from .约定.种子 import 向导种类,页面地址#向导种子

__all__=['可关闭标签','独一停靠标签','创建表面','创建右侧侧栏存储']#仅中文公开名


def 计数铸造(起点):
    """带用量回读的铸造。"""
    计数=[起点]#可变盒

    def 铸造(前缀):
        """前缀+序号。"""
        计数[0]+=1#加
        return 前缀+str(计数[0])#标识

    def 已用():
        """当前计数。"""
        return 计数[0]#数

    return 铸造,已用#铸造与用量


def _种子记录(标识,种子):
    """按当前默认页面铸造标签记录。"""
    初=种子()#种子 dict
    return {'id':标识,'kind':初['kind'],'title':初['title'],'contentId':页面地址(初['kind'])}#记录


def 可关闭标签(表面,标签标识):
    """显式关闭是否可移除该签：缺失或独一停靠向导不可关。"""
    签=表面['layout']['tabs'][标签标识] if 标签标识 in 表面['layout']['tabs'] else None#签
    return 签 is not None and not (签['kind']==向导种类 and 独一停靠标签(表面['layout'],标签标识))#可关


def 创建表面():
    """会话冷启动表面：折叠、单窗、无签。默认页在展开且空时由落定播种。"""
    铸造,已用=计数铸造(0)#铸造
    return {#表面
        'layout':创建初始状态(铸造),#无签初态
        'history':{'entries':list(空历史['entries']),'cursor':空历史['cursor']},#拷空历史
        'minted':已用(),
    }#表面


def _窗页面(状态,窗格标识,种类):
    """窗内该种类页面签，若有。"""
    return 查找窗格内容标签(状态,窗格标识,页面地址(种类),种类)#签


def _页面种类(状态,标签标识):
    """签所展示页面的种类；资源签为 None。"""
    签=状态['tabs'][标签标识] if 标签标识 in 状态['tabs'] else None#签
    if 签 is None:#无
        return None#无
    return 签['kind'] if 签['contentId']==页面地址(签['kind']) else None#页面种类


def 独一停靠标签(状态,标签标识):
    """是否为停靠面唯一签。"""
    窗=查找标签窗格(状态,标签标识)#窗
    return 窗['host']=='dock' and len(窗['tabs'])==1 and len(停靠窗格标识列表(状态))==1#独一


def _规划聚焦标签(状态,标签标识):
    """已是活动窗活动签则空。"""
    窗=查找标签窗格(状态,标签标识)#窗
    if 窗['activeTabId']==标签标识 and 状态['activePaneId']==窗['id']:#已焦
        return []#空
    return [{'type':'focusTab','tabId':标签标识}]#焦


def _规划聚焦窗格(状态,窗格标识):
    """已活动则空。"""
    if 状态['activePaneId']==窗格标识:#已
        return []#空
    return [{'type':'focusPane','paneId':窗格标识}]#焦


def _抵达(状态,标签标识,到窗,否则):
    """页面抵达已有同种页面窗则合并。"""
    种类=_页面种类(状态,标签标识)#页面种类
    if 种类 is None:#资源签
        return 否则()#原规划
    已有=_窗页面(状态,到窗,种类)#已有
    if 已有 is None or 已有==标签标识:#无冲突
        return 否则()#原
    return [{'type':'closeTab','tabId':标签标识},{'type':'focusTab','tabId':已有}]#合并


def _推进(表面,规划,种子):
    """跑规划、落定、记一条历史。"""
    铸造,已用=计数铸造(表面['minted'])#铸造
    def 造签(标识):
        """默认页签。"""
        return _种子记录(标识,种子)#记录
    已规划=规划(表面['layout'],铸造,造签)#操作
    if 已规划 is None or len(已规划)==0:#无变
        return 表面#原样
    之后=回放(表面['layout'],已规划)#草稿态
    落定=规划落定(之后,铸造,造签 if 之后['expanded'] else None)#展开才播种
    步进=记录(表面['history'],表面['layout'],list(已规划)+list(落定))#记
    return {'layout':步进['state'],'history':步进['history'],'minted':已用()}#次表面


def _落座(状态,会话标识,下一步):
    """换一会话表面，其它会话引用保留。"""
    表=状态['bySession']#表
    已有=表[会话标识] if 会话标识 in 表 else None#已有
    更新=下一步(已有 if 已有 is not None else 创建表面())#下一步
    if 更新 is 已有:#未变
        return 表#原表
    新表=dict(表)#拷
    新表[会话标识]=更新#写
    return 新表#新表


def _历史步进(表面,步进函):
    """undo/redo 单向。"""
    动=步进函(表面['history'],表面['layout'])#动
    if 动 is None:#无
        return 表面#原
    return {'layout':动['state'],'history':动['history'],'minted':表面['minted']}#表面


def 创建右侧侧栏存储(种子):
    """声明存储规格并带 create；种子为默认页面 thunk，每次铸造现读。"""

    def 初值():
        """空会话表。"""
        return {'bySession':{}}#初态

    def 打开(草稿,会话标识):
        """物化表面不改内容。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表面:表面)#落座

    def 设展开(草稿,会话标识,展开):
        """设展开。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:规划设展开(态,展开),种子))#推

    def 切换展开(草稿,会话标识):
        """翻转展开。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:规划设展开(态,not 态['expanded']),种子))#推

    def 设模式(草稿,会话标识,模式):
        """设呈现模式。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:规划设模式(态,模式),种子))#推

    def 分窗格(草稿,会话标识,窗格标识=None,落定回调=None):
        """分窗格；落定回调同步报告新窗。"""
        def 下一步(表):
            """推进并回调。"""
            def 规划(态,铸,造签):
                """预算内才分。"""
                if len(停靠窗格标识列表(态))>=2:#已两格
                    return []#空
                目标=窗格标识 if 窗格标识 is not None else 活动停靠窗格标识(态)#目标窗
                if len(取窗格(态,目标)['tabs'])==0:#空窗不分
                    return []#空
                return 规划分窗格(态,铸,窗格标识,造签)#分
            次=_推进(表,规划,种子)#次
            if 落定回调 is not None and 次 is not 表:#有新建
                前=set(停靠窗格标识列表(表['layout']))#前
                for 标识 in 停靠窗格标识列表(次['layout']):#后
                    if 标识 not in 前:#新
                        落定回调(标识)#报
            return 次#次
        草稿['bySession']=_落座(草稿,会话标识,下一步)#落座

    def 打开内容(草稿,会话标识,意图,落定回调):
        """打开内容并回调落点签。"""
        def 规划(态,铸,_造签):
            """合成展开+开/焦+可选关替。"""
            操作=list(规划设展开(态,True))#先展开
            替换=意图['replaceTab'] if 'replaceTab' in 意图 else None#替
            被替=查找标签窗格(态,替换) if 替换 is not None else None#被替窗
            借=被替 if 替换 is not None and 被替 is not None and 被替['host']=='dock' else None#可借
            窗=借['id'] if 借 is not None else (意图['paneId'] if 'paneId' in 意图 else None)#窗
            下标=None if 借 is None or 替换 is None else 借['tabs'].index(替换)#槽
            种类=意图['kind']#种类
            内容=意图['contentId']#内容
            页面=内容==页面地址(种类)#是否页面
            持有=_窗页面(态,窗 if 窗 is not None else 活动停靠窗格标识(态),种类) if 页面 else None#页唯一
            if 持有 is not None:#焦已有页面
                规划果={'ops':[{'type':'focusTab','tabId':持有}],'tabId':持有}#焦
            else:#常规开
                入={'kind':种类,'contentId':内容,'title':意图['title']}#入
                if 窗 is not None:#有窗
                    入['paneId']=窗#窗
                if 下标 is not None:#有槽
                    入['index']=下标#槽
                if 页面:#页面不跨窗揭示
                    入['revealIfOpened']=False#关揭示
                elif 'revealIfOpened' in 意图:#资源揭示
                    入['revealIfOpened']=意图['revealIfOpened']#写
                规划果=规划打开内容(态,铸,入)#开
            操作.extend(规划果['ops'])#并
            if 替换 is not None and 替换!=规划果['tabId']:#关替
                操作.append({'type':'closeTab','tabId':替换})#关
            落定回调(规划果['tabId'])#报
            return 操作#操作
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,规划,种子))#落座

    def 复制标签(草稿,会话标识,标签标识):
        """页面不复制。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,铸,_造:([] if _页面种类(态,标签标识) is not None else 规划复制标签(态,铸,标签标识)['ops']),种子))#推

    def 关闭标签(草稿,会话标识,标签标识):
        """关闭；独一非向导则连同收起列。"""
        def 规划(态,_铸,_造):
            """关规则。"""
            if not 可关闭标签({'layout':态},标签标识):#不可
                return []#空
            if not 独一停靠标签(态,标签标识):#非独一
                return [{'type':'closeTab','tabId':标签标识}]#关
            return [{'type':'closeTab','tabId':标签标识}]+list(规划设模式(态,'push'))+list(规划设展开(态,False))#关并收起
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,规划,种子))#落座

    def 聚焦标签(草稿,会话标识,标签标识):
        """焦签。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:_规划聚焦标签(态,标签标识),种子))#推

    def 聚焦窗格(草稿,会话标识,窗格标识):
        """焦窗。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:_规划聚焦窗格(态,窗格标识),种子))#推

    def 安置标签(草稿,会话标识,标签标识,到窗,下标):
        """安置。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,_,_造:_抵达(态,标签标识,到窗,lambda:规划安置标签(态,标签标识,到窗,下标)),种子))#推

    def 投放标签(草稿,会话标识,标签标识,窗格标识,区):
        """投放。"""
        def 规划(态,铸,造签):
            """区规则。"""
            if 区=='top' or 区=='bottom':#竖边本产品禁用
                return []#空
            if 区!='center' and len(停靠窗格标识列表(态))>=2:#边沿且已两格
                return []#空
            def 原():
                """套件规划。"""
                return 规划投放标签(态,铸,标签标识,窗格标识,区,造签)#投
            return _抵达(态,标签标识,窗格标识,原) if 区=='center' else 原()#中心合并
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,规划,种子))#落座

    def 浮出标签(草稿,会话标识,标签标识,矩形=None):
        """浮出。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda 态,铸,_造:规划浮出标签(态,铸,标签标识,矩形)['ops'],种子))#推

    def 收回浮窗(草稿,会话标识,窗格标识):
        """收回；页面合并。"""
        def 规划(态,_铸,_造):
            """合并规则。"""
            浮签=取窗格(态,窗格标识)['tabs'][0] if len(取窗格(态,窗格标识)['tabs'])>0 else None#浮签
            def 原():
                """套件收回。"""
                return 规划收回浮窗(态,窗格标识)#收
            if 浮签 is None:#无签
                return 原()#原
            return _抵达(态,浮签,活动停靠窗格标识(态),原)#合并
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,规划,种子))#落座

    def 移动浮窗(草稿,会话标识,窗格标识,横,纵):
        """移浮。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda *_:[{'type':'moveFloat','paneId':窗格标识,'x':横,'y':纵}],种子))#推

    def 调整浮窗(草稿,会话标识,窗格标识,矩形):
        """调浮。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda *_:[{'type':'resizeFloat','paneId':窗格标识,'rect':矩形}],种子))#推

    def 调整分割(草稿,会话标识,分割标识,尺寸表):
        """调分割。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_推进(表,lambda *_:规划调整分割(分割标识,尺寸表,0.2),种子))#推

    def 撤销(草稿,会话标识):
        """后退。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_历史步进(表,后退一步))#退

    def 重做(草稿,会话标识):
        """前进。"""
        草稿['bySession']=_落座(草稿,会话标识,lambda 表:_历史步进(表,前进一步))#进

    动作表={#写集合；线协议动作键保持英文
        'open':打开,
        'setExpanded':设展开,
        'toggleExpanded':切换展开,
        'setMode':设模式,
        'splitPane':分窗格,
        'openContent':打开内容,
        'duplicateTab':复制标签,
        'closeTab':关闭标签,
        'focusTab':聚焦标签,
        'focusPane':聚焦窗格,
        'placeTab':安置标签,
        'dropTab':投放标签,
        'floatTab':浮出标签,
        'unfloatPane':收回浮窗,
        'moveFloat':移动浮窗,
        'resizeFloat':调整浮窗,
        'resizeSplit':调整分割,
        'undo':撤销,
        'redo':重做,
    }#动作结束

    def 铸造(作用域键=None):
        """铸造可观察实例；作用域键由槽运行时传入。"""
        状态=初值()#态
        监听者=[]#订阅

        def 通知():
            """扇出。"""
            for 监听 in list(监听者):#快照
                监听()#回调

        def 取快照():
            """当前状态引用。"""
            return 状态#态

        def 订阅(监听):
            """登记。"""
            监听者.append(监听)#加
            def 拆除():
                """退订。"""
                if 监听 in 监听者:#仍在
                    监听者.remove(监听)#删
            return 拆除#拆除器

        def 绑(名,函):
            """绑定动作：写草稿后通知。"""
            def 调用(*参数):
                """调用。"""
                函(状态,*参数)#写
                通知()#广播
            return 调用#绑定

        return {#实例
            'getSnapshot':取快照,
            'subscribe':订阅,
            'actions':{名:绑(名,函) for 名,函 in 动作表.items()},
            'scopeKey':作用域键,
        }#实例

    return {'init':初值,'actions':动作表,'create':铸造}#规格+工厂

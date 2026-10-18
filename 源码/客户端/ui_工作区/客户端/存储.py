'浏览区查看存储。分组、排序、展开、手动顺序和归档筛选都写在这一份里'
from ...存储 import 声明存储
from .树 import 调和手动顺序

__all__=['扁平会话顺序键','创建工作区查看存储']

扁平会话顺序键='__flat_session_order__'#无层级扁平列表的本地账本键

def 拷会话顺序(顺序表):
    '把只读顺序拷成可写入的列表'
    return {键:list(顺序) for 键,顺序 in 顺序表.items()}#逐账本拷贝

def 初值():
    '默认按工作区分组、按最近更新，归档筛选为 default'
    return {
        'groupBy':'workspace',#分组
        'orderBy':'updated',#排序
        'groupExpansion':{},#展开
        'sessionOrderByAccount':{},#手动顺序
        'archivedFilter':'default',#归档筛选
    }

def 设分组(草稿,模式):
    '写入 groupBy'
    草稿['groupBy']=模式#分组

def 设排序(草稿,模式,初始顺序):
    '切入手动时拷入当前顺序，切回最近更新则清空账本'
    if 模式==草稿['orderBy']:#没变
        return#不动
    草稿['sessionOrderByAccount']=拷会话顺序(初始顺序) if 模式=='manual' else {}#账本
    草稿['orderBy']=模式#排序

def 设分组展开(草稿,键,展开):
    '写入某一个分组是否展开'
    草稿['groupExpansion'][键]=展开#展开

def 保留账本键(草稿,工作区键集合):
    '只留下仍存在的账本，并丢掉旧的时间戳账本'
    保留=set(工作区键集合)#仍在的键
    草稿['groupExpansion']={键:值 for 键,值 in 草稿['groupExpansion'].items() if 键 in 保留}#展开
    草稿['sessionOrderByAccount']={键:值 for 键,值 in 草稿['sessionOrderByAccount'].items() if 键 in 保留}#顺序
    if 'sessionUpdatedAtByAccount' in 草稿:#旧字段
        del 草稿['sessionUpdatedAtByAccount']#丢掉

def 同步会话顺序(草稿,顺序表):
    '只在手动排序时把顺序合并进账本'
    if 草稿['orderBy']!='manual':#不是手动
        return#不写
    草稿['sessionOrderByAccount'].update(拷会话顺序(顺序表))#合并

def 设会话顺序(草稿,账本键,顺序,初始顺序):
    '从最近更新切入手动时先铺全表，再写这一本'
    if 草稿['orderBy']=='updated':#从近因切入
        草稿['sessionOrderByAccount']=拷会话顺序(初始顺序)#铺全表
    else:#已经是手动
        草稿['sessionOrderByAccount'].update(拷会话顺序(初始顺序))#先对齐其它账本
    草稿['orderBy']='manual'#改为手动
    草稿['sessionOrderByAccount'][账本键]=list(顺序)#这一本

def 置顶会话顺序(草稿,会话号,账本键列,来源):
    '被置顶的会话排到它所属账本的最前，其它账本只做调和'
    选中=set(账本键列)#要提前的账本
    成员表=来源['members']#各账本成员
    摘要=来源['summaries']#会话摘要
    行态=来源['rowState']#置顶与归档
    下一={}#新账本
    for 键,成员 in 成员表.items():#逐账本
        顺序=调和手动顺序(成员,草稿['sessionOrderByAccount'].get(键),摘要,行态)#调和
        if 键 in 选中:#这一本要置顶
            下一[键]=[会话号]+[标识 for 标识 in 顺序 if 标识!=会话号]#排到最前
        else:#其它账本
            下一[键]=顺序#保持调和结果
    草稿['sessionOrderByAccount']=下一#写回

def 设归档筛选(草稿,筛选):
    '写入归档行的可见性'
    草稿['archivedFilter']=筛选#筛选

def 创建工作区查看存储():
    '返回浏览区查看存储句柄。登记时由渲染器创建一份实例'
    return 声明存储({
        'init':初值,#初值
        'persist':'dsh.workspace.view.v5',#持久化键
        'actions':{#动作名保持上游
            'setGroupBy':设分组,#分组
            'setOrderBy':设排序,#排序
            'setGroupExpanded':设分组展开,#展开
            'retainAccountKeys':保留账本键,#保留键
            'syncSessionOrders':同步会话顺序,#同步
            'setSessionOrder':设会话顺序,#写一本
            'pinSessionOrder':置顶会话顺序,#置顶提前
            'setArchivedFilter':设归档筛选,#归档筛选
        },
    })

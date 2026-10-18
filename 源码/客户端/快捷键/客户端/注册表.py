'命令注册、规范化默认绑定与同步分发'
from types import SimpleNamespace as 简易命名空间#目录与配置的只读面
from ...存储 import 创建快照存储#可观察快照
from ..异常 import 快捷键错误,抛出重复快捷键命令#登记拒绝
from ..协议 import (#协议
    绑定问题,
    绑定键,
    有效快捷键,
    初始快捷键配置,
    Web绑定是否准入,
    规范化绑定,
    绑定重叠,
    呈现绑定,
    解析快捷键默认,
)

__all__=['快捷键注册表']

class 快捷键注册表:
    '应用命令注册表。适配器拥有监听器，功能插件拥有动作'
    def __init__(自身,运行时,平台,配置=None):
        '播种可观察目录与配置'
        自身.runtime=运行时#壳
        自身.platform=平台#设备
        if 配置 is None:#缺省就绪空配置
            配置={**初始快捷键配置(),'status':'ready'}#就绪
        自身.命令表={}#id → 命令
        自身.固定表={}#id → 固定命令
        自身.冲突表={}#绑定键 → 命令
        自身.绑定表={}#绑定键 → 命令
        自身.状态=创建快照存储({'catalog':[],'config':配置})#联合快照

        def 取目录快照():
            '当前目录快照'
            return 自身.状态.getSnapshot()['catalog']

        def 取配置快照():
            '当前配置快照'
            return 自身.状态.getSnapshot()['config']

        自身.catalog=简易命名空间(getSnapshot=取目录快照,subscribe=自身.状态.subscribe)#目录面
        自身.config=简易命名空间(getSnapshot=取配置快照,subscribe=自身.状态.subscribe)#配置面
        自身.fixedCatalog=创建快照存储([])#固定目录

    def definitions(自身):
        '供存储校验的可序列化活跃目录，不含回调与本地化标签'
        表=[]#定义表
        for 命令 in 自身.命令表.values():#可编辑
            表.append({'id':命令['id'],'defaults':命令['defaults']})#定义
        for 命令 in 自身.固定表.values():#固定
            表.append({'id':命令['id'],'defaults':{},'fixed':命令['bindings']})#固定定义
        return 表#目录

    def registerFixed(自身,命令):
        '注册只读输入动作，其键不可分配给可编辑命令'
        标识=命令['id']#id
        if 标识 in 自身.固定表 or 标识 in 自身.命令表:#重复
            抛出重复快捷键命令(标识)#拒绝
        for 候选项 in 命令['bindings']:#校验物理码
            规范化绑定(候选项,自身.platform)#规范
        自身.固定表[标识]=命令#登记
        自身.refreshLabels()#刷新

        def 拆除():
            '幂等拆除这一份固定命令'
            if 自身.固定表.get(标识) is not 命令:#已换代
                return#跳过
            del 自身.固定表[标识]#删除
            自身.refreshLabels()#刷新

        return 拆除#拆除器

    def 刷新固定标签(自身):
        '重算固定目录行'
        行表=[]#固定行
        for 命令 in 自身.固定表.values():#逐固定
            行表.append({
                'id':命令['id'],
                'label':命令['label'](),
                'keys':命令['keys'],
                'group':命令['group'],
                'bindings':[规范化绑定(项,自身.platform) for 项 in 命令['bindings']],
            })
        自身.fixedCatalog.set(行表)#发布

    def configure(自身,配置):
        '原子发布已接受偏好与全部派生标签'
        当前=自身.config.getSnapshot()#当前
        if 配置['revision']==当前['revision'] and 配置['status']==当前['status'] and 配置['error']==当前['error']:#未变
            return#跳过
        自身.refreshLabels(配置)#刷新

    def register(自身,命令):
        '在检查各平台与壳的默认后原子注册'
        标识=命令['id']#id
        if 标识 in 自身.命令表 or 标识 in 自身.固定表:#重复
            抛出重复快捷键命令(标识)#拒绝
        for 运行时 in ('desktop','web'):#双壳
            for 平台 in ('macos','windows','linux'):#三平台
                候选=解析快捷键默认(命令,运行时,平台)#默认
                if 候选 is None:#无
                    continue#跳过
                绑定=规范化绑定(候选,平台)#规范
                if 运行时=='web' and not Web绑定是否准入(绑定,平台):#Web 拒
                    raise 快捷键错误('Unsupported Web shortcut: '+标识)#拒绝
                if 绑定问题(绑定,运行时,平台) is not None:#预留
                    raise 快捷键错误('Reserved shortcut default: '+标识)#拒绝
                for 已有 in 自身.命令表.values():#与已有
                    他候选=解析快捷键默认(已有,运行时,平台)#他默认
                    if 他候选 is None:#无
                        continue#跳过
                    if 绑定重叠(绑定,规范化绑定(他候选,平台)):#冲突
                        raise 快捷键错误('Conflicting shortcut defaults: '+标识+' and '+已有['id']+' ('+运行时+':'+平台+')')#拒绝
        自身.命令表[标识]=命令#登记
        自身.refreshLabels()#刷新

        def 拆除():
            '幂等拆除这一份命令'
            if 自身.命令表.get(标识) is not 命令:#已换代
                return#跳过
            del 自身.命令表[标识]#删除
            自身.refreshLabels()#刷新

        return 拆除#拆除器

    def refreshLabels(自身,配置=None):
        '偏好、命令或语言变化时重算有效绑定'
        if 配置 is None:#缺省当前
            配置=自身.config.getSnapshot()#当前
        自身.绑定表.clear()#清匹配
        自身.冲突表.clear()#清冲突
        行表=有效快捷键(自身.definitions(),配置['document'],自身.runtime,自身.platform)#有效
        目录=[]#目录行
        for 行 in 行表:#逐行
            命令=自身.命令表[行['id']]#命令
            启用=配置['status']!='loading' and 行['issue'] is None and len(行['conflicts'])==0#可执行
            if 启用 and 行['binding'] is not None:#可匹配
                自身.绑定表[绑定键(行['binding'])]=命令#登记
            if 配置['status']!='loading' and 行['issue'] is None and len(行['conflicts'])>0 and 行['binding'] is not None:#可见冲突
                自身.冲突表[绑定键(行['binding'])]=命令#登记冲突
            呈现=呈现绑定(行['binding'],自身.platform)#键帽
            目录.append({
                'id':行['id'],
                'label':命令['label'](),
                'aliases':命令['aliases'],
                'keys':呈现['keys'],
                'aria':呈现['aria'] if 启用 else None,
                'binding':行['binding'],
                'modified':行['modified'],
                'conflicts':行['conflicts'],
                'issue':行['issue'],
            })
        自身.状态.set({'config':配置,'catalog':目录})#原子发布
        自身.刷新固定标签()#固定

    def invoke(自身,标识,上下文):
        '调用原生菜单选择，独立于可选键绑定'
        命令=自身.命令表.get(标识)#命令
        if 命令 is None:#未登记
            return#跳过
        模态=上下文['modal']#模态
        if 模态 is not None and 模态 not in 命令['modals']:#模态不允许
            return#跳过
        结果=命令['resolve']({**上下文,'source':'menu'})#解析
        if 结果['status']=='handled':#已处理
            结果['run']()#执行

    def dispatch(自身,手势,上下文,消费):
        'Windows 与 macOS 桌面绑定覆盖局部区域和模态，与配置来源无关'
        if 手势['defaultPrevented'] or 手势['composing']:#已消费或组合
            return {'status':'pass'}#放过
        修饰=[项 for 项 in ('control','alt','shift','meta') if 手势[项]]#按下的修饰
        对键材料={'code':手势['code'],'modifiers':修饰}#材料
        if 手势.get('secondCode') is not None:#有次键
            对键材料['secondCode']=手势['secondCode']#次码
        对键=绑定键(对键材料)#对键索引
        if 对键 in 自身.绑定表 or 对键 in 自身.冲突表:#命中对键
            键=对键#用对键
        else:#回落单键
            键=绑定键({'code':手势['code'],'modifiers':修饰})#单键
        命令=自身.绑定表.get(键)#优先可执行
        if 命令 is None:#无
            命令=自身.冲突表.get(键)#冲突行
        优先=自身.runtime=='desktop' and (自身.platform=='windows' or 自身.platform=='macos')#桌面优先
        if 命令 is None or (not 优先 and 上下文['region'] not in 命令['regions']):#无命令或区域不符
            return {'status':'pass'}#放过
        if not 优先 and 上下文['region']=='terminal' and 手势['control'] and not 手势['meta'] and not 手势['alt'] and not 手势['shift'] and 手势['code'] in ('KeyW','KeyR'):#终端 Ctrl+W/R
            return {'status':'pass'}#放过
        if 键 not in 自身.绑定表:#仅冲突
            消费()#消费
            return {'status':'blocked','commandId':命令['id'],'reason':'conflict'}#冲突
        if not 优先 and 上下文['modal'] is not None and 上下文['modal'] not in 命令['modals']:#模态
            消费()#消费
            return {'status':'blocked','commandId':命令['id'],'reason':'modal'}#模态
        解析=命令['resolve'](上下文)#业务解析
        if 解析['status']=='pass':#放过
            return 解析#pass
        消费()#消费
        if 解析['status']=='blocked':#阻塞
            return {**解析,'commandId':命令['id']}#带 id
        if not 手势['repeat']:#非重复才跑
            解析['run']()#执行
        return {'status':'handled','commandId':命令['id']}#已处理

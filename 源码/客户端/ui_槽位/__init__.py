'槽位登记表纯核：普通槽、可复用工厂、存储座位和活拓扑'
import threading#微任务近似
from . import 存储,渲染器,异常#同目录模块，导入即执行顶层
from .异常 import 槽位错误,过期授权错误,槽位所有权错误#登记失败与渲染授权
from .渲染器 import 标准钩子属性名#钩子属性名

__all__=['槽位登记表','解析槽标签','标准钩子属性名','槽位错误','过期授权错误','槽位所有权错误','存储','渲染器','异常']#包内公开名

空条目=tuple()#未声明或已塌缩时共用的空台账


def 排微任务(函数):
    '把回调排到当前同步段结束之后'
    定时器=threading.Timer(0,函数)#近似 queueMicrotask
    定时器.start()#启动


def 解析槽标签(标签):
    '读取时解析列表标签。函数则调用，其余原样返回'
    if callable(标签):#零参函数
        return 标签()#此刻的文案
    return 标签#字面量或 None


class 槽位登记表:
    'root 槽是唯一先验声明，构造时播种为 single/root'
    def __init__(自身):
        '播种 root。此时无人观察，不标脏'
        自身.记录表={}#槽键到记录，创建后不删
        自身.工厂表={}#工厂名到记录，创建后不删
        自身.变更监听=set()#每次变更同步通知
        自身.句柄作用域={}#共享句柄身份到作用域和计数
        自身.脏表={}#待冲刷记录，键是身份编号
        自身.已排冲刷=False#是否已排微任务冲刷
        自身.已退位=[]#崩溃退位的条目，按对象身份
        自身.条目错误监听=set()#条目和工厂崩溃
        根记录=自身.取记录('root')#取得或创建 root
        根记录['spec']={'kind':'single','scope':'root'}#单占、根作用域
        根记录['declaredBy']='(built-in)'#框架内置
        根记录['declarationEpoch']=1#首次声明世代

    def 登记工厂(自身,选项,组件):
        '登记一条可复用工厂。已有定义或子槽冲突则失败。返回拆除器'
        名称=选项['name']#工厂名
        记录=自身.取工厂记录(名称)#空白记录也会留下
        if 记录['definition'] is not None:#已有定义
            raise 槽位错误(f"slot factory \"{名称}\" already has a definition")#重复定义
        #先拒绝已声明的子槽，再钉存储、写入定义
        if 'children' in 选项 and 选项['children'] is not None:#有子表
            子表=选项['children']#子槽声明
        else:#缺席
            子表=None#不声明
        if 子表 is not None:#逐个检查
            for 子键 in 子表.keys():#每个子键
                if 子键 not in 自身.记录表:#还没记录
                    continue#可以声明
                子记录=自身.记录表[子键]#已有记录
                if 子记录['spec'] is None:#还没声明
                    continue#可以声明
                if 子记录['declaredBy'] is not None:#有声明者
                    声明者=子记录['declaredBy']#原声明者
                else:#没有名字
                    声明者='an unknown entry'#未知
                raise 槽位错误(f"slot \"{子键}\" is already declared (by {声明者})")#一槽一声明者
        if 'store' in 选项 and 选项['store'] is not None:#有存储
            存储位=选项['store']#存储座位
        else:#没有
            存储位=None#不钉
        作用域=选项['scope']#工厂作用域
        if 存储位 is not None and callable(存储位) is False:#共享句柄
            标识=id(存储位)#对象身份
            if 标识 in 自身.句柄作用域:#已钉
                钉住=自身.句柄作用域[标识]#已有钉
            else:#未钉
                钉住=None#无
            if 钉住 is not None and 钉住['scope']!=作用域:#跨作用域
                已有作用域=钉住['scope']#已钉作用域
                raise 槽位错误(f"store handle mounted under factory \"{名称}\" (scope \"{作用域}\") is already mounted under scope \"{已有作用域}\" — one handle, one scope")#一柄一作用域
            if 钉住 is not None:#同一作用域
                钉住['count']+=1#加计数
            else:#首次
                自身.句柄作用域[标识]={'scope':作用域,'count':1}#钉住
        定义={'name':名称,'component':组件,'scope':作用域}#已存工厂
        if 子表 is not None:#子槽
            定义['children']=子表#children
        if 存储位 is not None:#存储
            定义['store']=存储位#store
        if 'inject' in 选项 and 选项['inject'] is not None:#注入
            定义['inject']=选项['inject']#inject
        if 'locale' in 选项 and 选项['locale'] is not None:#文案
            定义['locale']=选项['locale']#locale
        if 'slots' in 选项 and 选项['slots'] is not None:#局部位置
            定义['slots']=选项['slots']#slots
        if 'registrant' in 选项 and 选项['registrant'] is not None:#诊断
            定义['registrant']=选项['registrant']#registrant
        记录['definition']=定义#写入
        自身.标工厂脏(记录)#定义变更
        #子声明全部写完再标脏、再通知
        本批=[]#攒齐的子记录
        if 'registrant' in 选项:#登记方
            登记方=选项['registrant']#原值
        else:#缺席
            登记方=None#无
        if 登记方 is None or 登记方=='':#空则不加点名
            后缀=''#无后缀
        else:#有登记方
            后缀=f' ({登记方})'#括号点名
        if 子表 is not None:#声明子槽
            for 子键,子规格 in 子表.items():#每个子槽
                子记录=自身.取记录(子键)#取得或创建
                子记录['spec']=子规格#规格
                子记录['declaredBy']=f'factory "{名称}"{后缀}'#声明者
                子记录['parent']=f'factory:{名称}'#父为工厂键
                子记录['declarationEpoch']=子记录['declarationEpoch']+1#抬世代
                本批.append((子键,子记录))#攒下
            for 一对 in 本批:#先全部标脏
                自身.标脏(一对[0],一对[1])#同步变更
            for 一对 in 本批:#再通知声明寿命
                自身.通知声明(一对[1])#同步

        def 拆除():
            '幂等。定义已换或已拆则空操作'
            if 记录['definition'] is not 定义:#不是这一份
                return#空操作
            记录['definition']=None#清定义
            自身.标工厂脏(记录)#定义变更
            if 'store' in 定义:#有存储字段
                定义存储=定义['store']#存储
            else:#没有
                定义存储=None#无
            if 定义存储 is not None and callable(定义存储) is False:#共享句柄
                存储标识=id(定义存储)#身份
                if 存储标识 in 自身.句柄作用域:#有钉
                    定义钉=自身.句柄作用域[存储标识]#钉
                    定义钉['count']-=1#减
                    if 定义钉['count']==0:#归零
                        del 自身.句柄作用域[存储标识]#拿掉
            if 'children' in 定义:#有子表
                定义子表=定义['children']#子表
            else:#没有
                定义子表=None#无
            自身.拆除子槽(定义子表)#塌缩子槽
        return 拆除#拆除器

    def 取工厂(自身,名称):
        '读取已登记工厂定义。缺席为 None'
        if 名称 not in 自身.工厂表:#没有记录
            return None#缺席
        return 自身.工厂表[名称]['definition']#定义

    def 工厂版本(自身,名称):
        '工厂定义的单调版本。没碰过为 0'
        if 名称 not in 自身.工厂表:#没有记录
            return 0#0
        return 自身.工厂表[名称]['version']#版本

    def 订阅工厂(自身,名称,回调):
        '订阅工厂定义的登记寿命。每次变更各排一次微任务'
        记录=自身.取工厂记录(名称)#取得或创建
        记录['listeners'].add(回调)#加入

        def 退订():
            '从集合拿掉这个回调'
            记录['listeners'].discard(回调)#删
        return 退订#退订器

    def 工厂仍存活(自身,定义):
        '保留的工厂定义是否仍是当前这一份'
        名称=定义['name']#工厂名
        if 名称 not in 自身.工厂表:#没有记录
            return False#死
        return 自身.工厂表[名称]['definition'] is 定义#同一对象

    def 登记(自身,选项,组件):
        '向已声明的槽贡献一条。未声明、同格同优先级或基数不符则失败。返回拆除器'
        名称=选项['name']#目标槽
        if 名称 in 自身.记录表:#有记录
            记录=自身.记录表[名称]#记录
        else:#没碰过
            记录=None#无
        if 记录 is None or 记录['spec'] is None:#未声明
            raise 槽位错误(f"slot \"{名称}\" is not declared (a parent entry's children table must declare it)")#未声明
        规格=记录['spec']#运行时规格
        if 'priority' in 选项 and 选项['priority'] is not None:#显式优先级
            优先级=选项['priority']#原值
        else:#缺省
            优先级=0#0 是合法遮蔽秩

        def 占用提示(占用者):
            '点名优先级和占用者'
            if 'registrant' in 占用者 and 占用者['registrant'] is not None:#有登记方
                点名=f" (registered by {占用者['registrant']})"#点名
            else:#没有
                点名=''#无
            return f"at priority {优先级}{点名} — register at a different priority to shadow it (lowest renders)"#提示

        #同格只在完全相同的优先级上失败，不同优先级可以遮蔽
        种类=规格['kind']#基数
        台账=list(记录['entries'])#当前台账
        if 种类=='single':#单占
            for 已有条目 in 台账:#扫已有
                已有形状=已有条目['options']#形状
                if 'priority' in 已有形状 and 已有形状['priority'] is not None:#有优先级
                    已有优先级=已有形状['priority']#原值
                else:#缺省
                    已有优先级=0#0
                if 已有优先级==优先级:#同优先级
                    raise 槽位错误(f"single slot \"{名称}\" already has a registration {占用提示(已有条目)}")#冲突
        elif 种类=='keyed':#按键
            if 'key' not in 选项 or 选项['key'] is None:#缺 key
                raise 槽位错误(f"keyed slot \"{名称}\" requires options.key")#缺键
            键值=选项['key']#字面键
            for 已有条目 in 台账:#扫已有
                已有形状=已有条目['options']#形状
                if 'key' in 已有形状:#有键
                    已有键=已有形状['key']#已有键
                else:#没有
                    已有键=None#无
                if 'priority' in 已有形状 and 已有形状['priority'] is not None:#有优先级
                    已有优先级=已有形状['priority']#原值
                else:#缺省
                    已有优先级=0#0
                if 已有键==键值 and 已有优先级==优先级:#同键同优先级
                    raise 槽位错误(f"keyed slot \"{名称}\" already has an entry for key \"{键值}\" {占用提示(已有条目)}")#冲突
        elif 种类=='list':#列表
            if 'id' not in 选项 or 选项['id'] is None:#缺 id
                raise 槽位错误(f"list slot \"{名称}\" requires options.id")#缺标识
            标识值=选项['id']#标识
            for 已有条目 in 台账:#扫已有
                已有形状=已有条目['options']#形状
                if 'id' in 已有形状:#有标识
                    已有标识=已有形状['id']#已有标识
                else:#没有
                    已有标识=None#无
                if 'priority' in 已有形状 and 已有形状['priority'] is not None:#有优先级
                    已有优先级=已有形状['priority']#原值
                else:#缺省
                    已有优先级=0#0
                if 已有标识==标识值 and 已有优先级==优先级:#同标识同优先级
                    raise 槽位错误(f"list slot \"{名称}\" already has an entry with id \"{标识值}\" {占用提示(已有条目)}")#冲突
        elif 种类=='chain':#链
            if 'select' not in 选项 or 选项['select'] is None:#缺选择器
                raise 槽位错误(f"chain slot \"{名称}\" requires options.select")#缺选择器
        if 'children' in 选项 and 选项['children'] is not None:#有子表
            子表=选项['children']#子槽声明
        else:#缺席
            子表=None#不声明
        if 子表 is not None:#空表也要走声明
            for 子键 in 子表.keys():#每个子键
                if 子键 not in 自身.记录表:#还没记录
                    continue#可以声明
                子记录=自身.记录表[子键]#已有记录
                if 子记录['spec'] is None:#还没声明
                    continue#可以声明
                if 子记录['declaredBy'] is not None:#有声明者
                    声明者=子记录['declaredBy']#原声明者
                else:#没有名字
                    声明者='an unknown entry'#未知
                raise 槽位错误(f"slot \"{子键}\" is already declared (by {声明者})")#一槽一声明者
        if 'store' in 选项 and 选项['store'] is not None:#有存储
            存储位=选项['store']#存储座位
        else:#没有
            存储位=None#不钉
        if 存储位 is not None and callable(存储位) is False:#共享句柄
            作用域=规格['scope']#本槽作用域
            标识=id(存储位)#对象身份
            if 标识 in 自身.句柄作用域:#已钉
                钉住=自身.句柄作用域[标识]#已有钉
            else:#未钉
                钉住=None#无
            if 钉住 is not None and 钉住['scope']!=作用域:#跨作用域
                已有作用域=钉住['scope']#已钉作用域
                raise 槽位错误(f"store handle mounted under \"{名称}\" (scope \"{作用域}\") is already mounted under scope \"{已有作用域}\" — one handle, one scope")#一柄一作用域
            if 钉住 is not None:#同一作用域
                钉住['count']+=1#加计数
            else:#首次
                自身.句柄作用域[标识]={'scope':作用域,'count':1}#钉住
        形状={}#kind 形状字段
        if 'key' in 选项 and 选项['key'] is not None:#键
            形状['key']=选项['key']#key
        if 'id' in 选项 and 选项['id'] is not None:#标识
            形状['id']=选项['id']#id
        if 'order' in 选项 and 选项['order'] is not None:#显示序
            形状['order']=选项['order']#order
        if 'label' in 选项 and 选项['label'] is not None:#标签
            形状['label']=选项['label']#label
        if 'priority' in 选项 and 选项['priority'] is not None:#遮蔽秩
            形状['priority']=选项['priority']#priority
        条目={'component':组件,'options':形状}#本条登记
        if 'select' in 选项 and 选项['select'] is not None:#链选择器
            条目['select']=选项['select']#select
        if 'inject' in 选项 and 选项['inject'] is not None:#业务面
            条目['inject']=选项['inject']#inject
        if 子表 is not None:#子槽
            条目['children']=子表#children
        if 存储位 is not None:#存储
            条目['store']=存储位#store
        if 'locale' in 选项 and 选项['locale'] is not None:#文案命名空间
            条目['locale']=选项['locale']#locale
        if 'registrant' in 选项 and 选项['registrant'] is not None:#诊断
            条目['registrant']=选项['registrant']#registrant
        下一批=台账+[条目]#追加

        def 列表键(一条):
            '列表先按优先级，再按显示序'
            一条形状=一条['options']#形状
            if 'priority' in 一条形状 and 一条形状['priority'] is not None:#有优先级
                一条优先级=一条形状['priority']#原值
            else:#缺省
                一条优先级=0#0
            if 'order' in 一条形状 and 一条形状['order'] is not None:#有显示序
                一条顺序=一条形状['order']#原值
            else:#缺省
                一条顺序=0#0
            return (一条优先级,一条顺序)#排序键

        def 优先级键(一条):
            '非列表只按优先级'
            一条形状=一条['options']#形状
            if 'priority' in 一条形状 and 一条形状['priority'] is not None:#有优先级
                return 一条形状['priority']#原值
            return 0#缺省

        if 种类=='list':#列表再按显示序
            下一批.sort(key=列表键)#优先级然后显示序
        else:#其余只按优先级
            下一批.sort(key=优先级键)#优先级升序，同分保持登记顺序
        记录['entries']=tuple(下一批)#写回台账
        自身.标脏(名称,记录)#标脏
        本批=[]#攒齐的子记录
        if 'registrant' in 选项:#登记方
            登记方=选项['registrant']#原值
        else:#缺席
            登记方=None#无
        if 登记方 is None or 登记方=='':#空则不加点名
            后缀=''#无后缀
        else:#有登记方
            后缀=f' ({登记方})'#括号点名
        if 子表 is not None:#声明子槽
            for 子键,子规格 in 子表.items():#每个子槽
                子记录=自身.取记录(子键)#取得或创建
                子记录['spec']=子规格#规格
                子记录['declaredBy']=f'an entry in "{名称}"{后缀}'#声明者
                子记录['parent']=名称#父槽
                子记录['declarationEpoch']=子记录['declarationEpoch']+1#抬世代
                本批.append((子键,子记录))#攒下
            for 一对 in 本批:#先全部标脏
                自身.标脏(一对[0],一对[1])#同步变更
            for 一对 in 本批:#再通知声明寿命
                自身.通知声明(一对[1])#同步

        def 拆除():
            '幂等。级联拆掉之后再调是空操作'
            仍在=False#是否还在台账
            for 当前条目 in 记录['entries']:#扫台账
                if 当前条目 is 条目:#同一对象
                    仍在=True#还在
                    break#停
            if 仍在 is False:#已经不在
                return#空操作
            留下=[]#剩余条目
            for 当前条目 in 记录['entries']:#再扫
                if 当前条目 is not 条目:#不是本条
                    留下.append(当前条目)#留下
            记录['entries']=tuple(留下)#写回
            自身.标脏(名称,记录)#标脏
            自身.拆除条目(条目)#卸存储和子槽
        return 拆除#拆除器

    def 仍存活(自身,条目):
        '这条登记是否还在任一槽的台账里'
        for 记录 in 自身.记录表.values():#每个槽
            for 当前条目 in 记录['entries']:#台账
                if 当前条目 is 条目:#同一对象
                    return True#活
        return False#死

    def 取条目列表(自身,槽键):
        '变更之间返回同一份台账'
        if 槽键 not in 自身.记录表:#没有记录
            return 空条目#空
        return 自身.记录表[槽键]['entries']#台账引用

    def 取槽位条目(自身,槽键):
        '每格的遮蔽胜者。chain 不遮蔽，原样返回台账'
        if 槽键 not in 自身.记录表:#没有记录
            return 空条目#空
        记录=自身.记录表[槽键]#记录
        if 记录['spec'] is None:#未声明
            return 空条目#空
        种类=记录['spec']['kind']#基数
        if 种类=='chain':#链用全部条目
            return 记录['entries']#台账引用
        胜者=[]#每格第一个还活着的
        已见格=set()#已经有胜者的格子
        for 当前条目 in 记录['entries']:#按优先级扫
            if 自身.已经退位(当前条目):#崩溃退位
                continue#跳过
            形状=当前条目['options']#形状
            if 种类=='keyed':#按键一格
                if 'key' in 形状:#有键
                    格子=形状['key']#键
                else:#没有
                    格子=None#共用缺键格
            elif 种类=='list':#按标识一格
                if 'id' in 形状:#有标识
                    格子=形状['id']#标识
                else:#没有
                    格子=None#共用缺标识格
            else:#single 共用一格
                格子=None#唯一格
            if 格子 in 已见格:#已有胜者
                continue#跳过
            已见格.add(格子)#记下
            胜者.append(当前条目)#胜者
        return 胜者#每次新列表

    def 规格(自身,槽键):
        '已声明的运行时规格。未声明为 None'
        if 槽键 not in 自身.记录表:#没有记录
            return None#无
        return 自身.记录表[槽键]['spec']#规格

    def 动态规格(自身,槽键):
        '只拿着字符串键时读取规格。未声明为 None'
        if 槽键 not in 自身.记录表:#没有记录
            return None#无
        return 自身.记录表[槽键]['spec']#规格

    def 快照(自身,根名=None):
        '导出活的槽和工厂拓扑。不含组件和可执行钩'
        def 建槽(槽名,已见):
            '成环或未声明则没有节点'
            if 槽名 not in 自身.记录表:#没有记录
                return None#无
            记录=自身.记录表[槽名]#记录
            if 记录['spec'] is None or 槽名 in 已见:#未声明或成环
                return None#无
            分支=set(已见)#祖先
            分支.add(槽名)#加上自己
            活动集=set()#胜出者身份
            for 胜出 in 自身.取槽位条目(槽名):#胜出
                活动集.add(id(胜出))#字典不能放进集合
            子节点=[]#子树
            for 子名,候选记录 in 自身.记录表.items():#全部记录
                if 候选记录['spec'] is not None and 候选记录['parent']==槽名:#活的子槽
                    子节=建槽(子名,分支)#递归
                    if 子节 is not None:#建成
                        子节点.append(子节)#记入
            占用者=[]#占用者
            for 当前条目 in 记录['entries']:#台账原文
                形状=当前条目['options']#形状
                占用行={}#一行
                if 'registrant' in 当前条目 and 当前条目['registrant'] is not None:#登记方
                    占用行['registrant']=当前条目['registrant']#带上
                if 'key' in 形状 and 形状['key'] is not None:#键
                    占用行['key']=形状['key']#键
                if 'id' in 形状 and 形状['id'] is not None:#标识
                    占用行['id']=形状['id']#标识
                if 'order' in 形状 and 形状['order'] is not None:#显示序
                    占用行['order']=形状['order']#序
                if 'priority' in 形状 and 形状['priority'] is not None:#优先级
                    占用行['priority']=形状['priority']#原值
                else:#缺省
                    占用行['priority']=0#0
                占用行['active']=id(当前条目) in 活动集#是否胜出
                占用者.append(占用行)#记入
            节点={'type':'slot','name':槽名,'kind':记录['spec']['kind'],'scope':记录['spec']['scope']}#槽节点
            if 记录['declaredBy'] is not None:#有声明者
                节点['declaredBy']=记录['declaredBy']#插在占用者前
            节点['occupants']=占用者#占用者
            节点['children']=子节点#子树
            return 节点#返回

        def 建工厂(工厂名):
            '没有定义则没有节点'
            if 工厂名 not in 自身.工厂表:#没有记录
                return None#无
            定义=自身.工厂表[工厂名]['definition']#定义
            if 定义 is None:#未登记
                return None#无
            父名='factory:'+str(工厂名)#子槽的父键
            子节点=[]#子树
            for 子名,候选记录 in 自身.记录表.items():#全部记录
                if 候选记录['spec'] is not None and 候选记录['parent']==父名:#工厂的子槽
                    子节=建槽(子名,set([父名]))#从工厂键起算
                    if 子节 is not None:#建成
                        子节点.append(子节)#记入
            节点={'type':'factory','name':工厂名,'scope':定义['scope']}#工厂节点
            if 'registrant' in 定义 and 定义['registrant'] is not None:#登记方
                节点['registrant']=定义['registrant']#带上
            节点['children']=子节点#子树
            return 节点#返回

        if 根名 is not None:#指定根
            if 根名.startswith('factory:'):#工厂根
                节点=建工厂(根名[len('factory:'):])#去掉前缀
            else:#普通槽根
                节点=建槽(根名,set())#从空已见起
            if 节点 is None:#不可用
                return []#空
            return [节点]#只有这一棵
        结果=[]#活根
        for 槽名,记录 in 自身.记录表.items():#全部槽
            if 记录['spec'] is not None and 记录['parent'] is None:#活的根槽
                节点=建槽(槽名,set())#建
                if 节点 is not None:#建成
                    结果.append(节点)#记入
        for 工厂名 in 自身.工厂表.keys():#全部工厂
            节点=建工厂(工厂名)#建
            if 节点 is not None:#建成
                结果.append(节点)#记入
        return 结果#槽在前，工厂在后

    def 声明世代(自身,槽键):
        '声明寿命。增减条目不改变它，没声明过为 0'
        if 槽键 not in 自身.记录表:#没有记录
            return 0#0
        return 自身.记录表[槽键]['declarationEpoch']#世代

    def 订阅(自身,槽键,回调):
        '订阅登记变更。微任务里合并通知，允许在声明前订阅'
        记录=自身.取记录(槽键)#取得或创建
        记录['listeners'].add(回调)#加入

        def 退订():
            '从集合拿掉这个回调'
            记录['listeners'].discard(回调)#删
        return 退订#退订器

    def 订阅声明(自身,槽键,回调):
        '订阅声明和塌缩。同步通知，普通条目变更不通知'
        记录=自身.取记录(槽键)#取得或创建
        记录['declarationListeners'].add(回调)#加入

        def 退订():
            '从集合拿掉这个回调'
            记录['declarationListeners'].discard(回调)#删
        return 退订#退订器

    def 版本(自身,槽键):
        '单调版本。没碰过为 0'
        if 槽键 not in 自身.记录表:#没有记录
            return 0#0
        return 自身.记录表[槽键]['version']#版本

    def 变更时(自身,回调):
        '每次变更同步通知，不合并'
        自身.变更监听.add(回调)#加入

        def 退订():
            '从集合拿掉这个回调'
            自身.变更监听.discard(回调)#删
        return 退订#退订器

    def 已经退位(自身,条目):
        '这条登记是否已经因为崩溃退出格子'
        for 已有条目 in 自身.已退位:#逐条
            if 已有条目 is 条目:#同一对象
                return True#已退
        return False#还在格子里

    def 报告条目错误(自身,槽键,条目,错误,信息):
        '遮蔽类崩溃可退位一次。重复退位整段空操作。链只通知'
        if 'abdicate' in 信息:#调用方给了字段
            退位值=信息['abdicate']#原值
        else:#缺席
            退位值=None#当未退位
        if 退位值:#真值才退位
            if 自身.已经退位(条目):#已经退过
                return#不再通知
            自身.已退位.append(条目)#记下
            if 槽键 in 自身.记录表:#有记录
                自身.标脏(槽键,自身.记录表[槽键])#抬版本
        for 回调 in list(自身.条目错误监听):#快照后通知
            回调(槽键,条目,错误,{'abdicated':退位值})#同步

    def 报告工厂错误(自身,名称,登记,错误):
        '工厂出现崩溃只通知，不退掉共享定义'
        键名='factory:'+str(名称)#监督通道上的键
        for 回调 in list(自身.条目错误监听):#快照后通知
            回调(键名,登记,错误,{'abdicated':False})#不退位

    def 条目错误时(自身,回调):
        '订阅条目和工厂崩溃。每次报告同步通知'
        自身.条目错误监听.add(回调)#加入

        def 退订():
            '从集合拿掉这个回调'
            自身.条目错误监听.discard(回调)#删
        return 退订#退订器

    def 拆除条目(自身,条目):
        '卸掉共享存储挂载，并塌缩它声明的子槽'
        if 'store' in 条目:#有存储字段
            存储位=条目['store']#存储
        else:#没有
            存储位=None#无
        if 存储位 is not None and callable(存储位) is False:#共享句柄
            标识=id(存储位)#身份
            if 标识 in 自身.句柄作用域:#有钉
                钉住=自身.句柄作用域[标识]#钉
                钉住['count']-=1#减
                if 钉住['count']==0:#归零
                    del 自身.句柄作用域[标识]#拿掉
        if 'children' in 条目:#有子表
            子表=条目['children']#子表
        else:#没有
            子表=None#无
        自身.拆除子槽(子表)#塌缩

    def 拆除子槽(自身,子表):
        '清掉子槽声明，并递归拆除子条目'
        if 子表 is None:#没有子表
            return#完
        for 子键 in 子表.keys():#每个子槽
            if 子键 not in 自身.记录表:#声明时本应已有记录
                continue#没有则跳过
            子记录=自身.记录表[子键]#子记录
            注定=list(子记录['entries'])#先抄出台账
            子记录['spec']=None#清规格
            子记录['declaredBy']=None#清声明者
            子记录['parent']=None#清父
            子记录['declarationEpoch']=子记录['declarationEpoch']+1#抬世代
            子记录['entries']=空条目#清空
            自身.标脏(子键,子记录)#标脏
            自身.通知声明(子记录)#同步通知塌缩
            for 死条目 in 注定:#递归
                自身.拆除条目(死条目)#卸

    def 取记录(自身,槽键):
        '第一次碰到时创建空白记录，之后永不删除'
        if 槽键 in 自身.记录表:#已有
            return 自身.记录表[槽键]#返回
        记录={}#空白
        记录['spec']=None#尚未声明
        记录['declaredBy']=None#无声明者
        记录['parent']=None#无父
        记录['declarationEpoch']=0#首次声明前
        记录['entries']=空条目#空台账
        记录['version']=0#未变更
        记录['listeners']=set()#登记变更
        记录['declarationListeners']=set()#声明寿命
        自身.记录表[槽键]=记录#写入
        return 记录#返回

    def 取工厂记录(自身,名称):
        '第一次碰到时创建空白工厂记录，之后永不删除'
        if 名称 in 自身.工厂表:#已有
            return 自身.工厂表[名称]#返回
        记录={}#空白
        记录['definition']=None#尚无定义
        记录['version']=0#未变更
        记录['listeners']=set()#定义变更
        自身.工厂表[名称]=记录#写入
        return 记录#返回

    def 标工厂脏(自身,记录):
        '抬工厂版本。每次变更各排一次微任务，不与槽位冲刷合并'
        记录['version']=记录['version']+1#抬版本

        def 稍后通知():
            '通知当时的订阅者'
            for 回调 in list(记录['listeners']):#快照
                回调()#通知
        排微任务(稍后通知)#排队

    def 标脏(自身,槽键,记录):
        '同步抬版本并通知变更。订阅合并到一次微任务'
        记录['version']=记录['version']+1#抬版本
        for 回调 in list(自身.变更监听):#同步、不合并
            回调(槽键)#变更键
        自身.脏表[id(记录)]=记录#记下，重复标脏不改顺序
        if 自身.已排冲刷:#已经排过
            return#不再排
        自身.已排冲刷=True#门闩

        def 稍后冲刷():
            '到点冲刷订阅'
            自身.冲刷()#冲刷
        排微任务(稍后冲刷)#排队

    def 通知声明(自身,记录):
        '同步通知声明寿命订阅者'
        for 回调 in list(记录['declarationListeners']):#快照
            回调()#通知

    def 冲刷(自身):
        '先复位，监听器里的变更可以重新排程'
        自身.已排冲刷=False#复位
        待冲=list(自身.脏表.values())#快照
        自身.脏表.clear()#清空
        for 待通知 in 待冲:#逐个脏记录
            for 回调 in list(待通知['listeners']):#快照监听
                回调()#通知

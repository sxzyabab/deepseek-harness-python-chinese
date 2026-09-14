import re#属性名合法性
from .模型 import 子类型节点标识列表#子边

__all__=[#仅中文公开名
    '类型图渲染错误','类型图渲染器',
]#公开面结束

class 类型图渲染错误(Exception):#类型图渲染错误
    """渲染或遍历内部不一致的 TypeGraph 时失败。"""
    name='TypeGraphRenderError'#错误名

def 引号(值):#单引号字符串
    """转义。"""
    return "'"+值.replace('\\','\\\\').replace("'","\\'").replace('\n','\\n')+"'"#字面量

def 转义模板(值):#转义模板字面量片段
    """反斜杠、反引号、插值。"""
    return 值.replace('\\','\\\\').replace('`','\\`').replace('${','\\${')#转义

def 渲染属性名(名):#渲染属性名
    """计算属性原样；合法标识或纯数字原样；其余加引号。"""
    if 名.startswith('[') and 名.endswith(']'):#计算属性
        return 名#原样
    if re.match(r'^(?:[$A-Z_a-z][$\w]*|\d+)$',名):#合法
        return 名#原样
    return 引号(名)#加引号

def 需要数组括号(节点):#数组元素是否需要括号
    """联合/函数等后缀 [] 会歧义。"""
    return 节点['kind'] in ('union','intersection','function','constructor','conditional')#需括号

def 收集节点签名(节点):#节点自带的签名
    """函数与构造各一条。"""
    return [节点['signature']] if 节点['kind'] in ('function','constructor') else []#签名

class 类型图渲染器:#类型图渲染器
    """在没有编译器对象的情况下读取并渲染一张 TypeGraph。"""
    def __init__(自身,图):#按完整图建索引
        """保留原图并建查找表。"""
        自身.graph=图#原图
        自身.节点表={节点['id']:节点 for 节点 in (图['nodes'] if 'nodes' in 图 else [])}#节点表
        自身.声明表={声明['id']:声明 for 声明 in (图['declarations'] if 'declarations' in 图 else [])}#声明表
        自身.成员表={}#成员表
        for 声明 in (图['declarations'] if 'declarations' in 图 else []):#跨声明
            for 成员 in (声明['members'] if 'members' in 声明 else []):#成员
                自身.成员表[成员['id']]=成员#登记
        自身.参数名={}#类型参数 id → 源码名
        for 声明 in (图['declarations'] if 'declarations' in 图 else []):#逐声明
            自身.索引参数(声明['typeParameters'] if 'typeParameters' in 声明 else [])#声明级
            for 成员 in (声明['members'] if 'members' in 声明 else []):#成员级
                if 'signature' in 成员:#有签名
                    签名=成员['signature'] if 成员['signature'] is not None else {}#签名
                    自身.索引参数(签名['typeParameters'] if 'typeParameters' in 签名 else [])#签名级

    def node(自身,标识):#按 id 取类型节点
        """缺节点即断边。"""
        节点=自身.节点表[标识] if 标识 in 自身.节点表 else None#查找
        if 节点 is None:#缺
            raise 类型图渲染错误('type graph references missing node '+str(标识))#断边
        return 节点#命中

    def declaration(自身,标识):#按符号 id 取声明
        """缺声明即断边。"""
        声明=自身.声明表[标识] if 标识 in 自身.声明表 else None#查找
        if 声明 is None:#缺
            raise 类型图渲染错误('type graph references missing declaration '+str(标识))#断边
        return 声明#命中

    def member(自身,标识):#按成员 id 取成员
        """缺成员即断边。"""
        成员=自身.成员表[标识] if 标识 in 自身.成员表 else None#查找
        if 成员 is None:#缺
            raise 类型图渲染错误('type graph references missing member '+str(标识))#断边
        return 成员#命中

    def renderType(自身,标识,引用=None):#渲染一条类型表达式
        """按种类分发。"""
        节点=自身.node(标识)#取出
        种类=节点['kind']#种类
        if 种类=='keyword':#关键字
            return 节点['name'] if 'name' in 节点 else None#名字
        if 种类=='literal':#字面量
            return 节点['text'] if 'text' in 节点 else None#文本
        if 种类=='parenthesized':#括号
            return '('+自身.renderType(节点['type'] if 'type' in 节点 else None,引用)+')'#包一层
        if 种类=='reference':#具名引用
            目标=节点['target'] if 'target' in 节点 else {}#目标
            目标种类=目标['kind'] if 'kind' in 目标 else None#目标种类
            节点名=节点['name'] if 'name' in 节点 else None#源名
            if 目标种类=='type-parameter':#类型参数
                参数标识=目标['parameter'] if 'parameter' in 目标 else None#类型参数 id
                名=自身.参数名[参数标识] if 参数标识 in 自身.参数名 else 节点名#参数名
            elif 目标种类=='declaration':#声明
                符号=目标['symbol'] if 'symbol' in 目标 else None#声明符号
                if isinstance(引用,dict) and 符号 in 引用:#有生成名
                    名=引用[符号]#生成名
                else:#无生成名
                    名=节点名#源名
            else:#其它
                名=节点名#源名
            实参=节点['arguments'] if 'arguments' in 节点 else []#实参
            if len(实参)==0:#无实参
                return 名#裸名
            return 名+'<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#带实参
        if 种类=='union':#联合
            return ' | '.join(自身.renderType(项,引用) for 项 in (节点['types'] if 'types' in 节点 else []))#|
        if 种类=='intersection':#交叉
            return ' & '.join(自身.renderType(项,引用) for 项 in (节点['types'] if 'types' in 节点 else []))#&
        if 种类=='array':#数组
            元素=自身.renderType(节点['element'] if 'element' in 节点 else None,引用)#元素
            包='('+元素+')' if 需要数组括号(自身.node(节点['element'] if 'element' in 节点 else None)) else 元素#括号
            return 包+'[]'#后缀
        if 种类=='tuple':#元组
            元素列表=[]#文本
            for 元素 in 节点['elements'] if 'elements' in 节点 else []:#逐元素
                类型=自身.renderType(元素['type'] if 'type' in 元素 else None,引用)#类型
                名=元素['name'] if 'name' in 元素 else None#名字
                rest='...' if ('rest' in 元素 and 元素['rest']) else ''#rest
                可选='?' if ('optional' in 元素 and 元素['optional']) else ''#可选
                if 名 is not None:#具名
                    元素列表.append(rest+名+可选+': '+类型)#具名
                else:#匿名
                    元素列表.append(rest+类型+可选)#匿名
            return '['+', '.join(元素列表)+']'#元组
        if 种类=='object':#对象
            return 自身.渲染对象(节点['members'] if 'members' in 节点 else [],引用)#对象
        if 种类=='function':#函数
            签名=节点['signature'] if 'signature' in 节点 else {}#签名
            return 自身.渲染签名头(签名,引用)+' => '+自身.renderType(签名['returns'] if 'returns' in 签名 else None,引用)#函数
        if 种类=='constructor':#构造
            签名=节点['signature'] if 'signature' in 节点 else {}#签名
            前='abstract ' if ('abstract' in 节点 and 节点['abstract']) else ''#abstract
            return 前+'new '+自身.渲染签名头(签名,引用)+' => '+自身.renderType(签名['returns'] if 'returns' in 签名 else None,引用)#构造
        if 种类=='indexed-access':#索引访问
            return 自身.renderType(节点['object'] if 'object' in 节点 else None,引用)+'['+自身.renderType(节点['index'] if 'index' in 节点 else None,引用)+']'#索引
        if 种类=='operator':#运算符
            return (节点['operator'] if 'operator' in 节点 else None)+' '+自身.renderType(节点['type'] if 'type' in 节点 else None,引用)#运算符
        if 种类=='conditional':#条件
            return (自身.renderType(节点['check'] if 'check' in 节点 else None,引用)+' extends '+自身.renderType(节点['extends'] if 'extends' in 节点 else None,引用)
                +' ? '+自身.renderType(节点['whenTrue'] if 'whenTrue' in 节点 else None,引用)+' : '+自身.renderType(节点['whenFalse'] if 'whenFalse' in 节点 else None,引用))#条件
        if 种类=='infer':#infer
            return 'infer '+自身.渲染类型参数(节点['parameter'] if 'parameter' in 节点 else {},False,引用)#infer
        if 种类=='mapped':#映射
            只读=节点['readonly'] if 'readonly' in 节点 else None#readonly
            只读前='' if 只读=='preserve' else ('-readonly ' if 只读=='remove' else 'readonly ')#修饰
            可选=节点['optional'] if 'optional' in 节点 else None#optional
            可选后='' if 可选=='preserve' else ('-?' if 可选=='remove' else '?')#修饰
            参数=节点['parameter'] if 'parameter' in 节点 else {}#参数
            约束=参数['constraint'] if 'constraint' in 参数 else None#约束
            if 约束 is None:#无约束
                raise 类型图渲染错误('mapped type parameter '+str(参数['name'] if 'name' in 参数 else None)+' has no constraint')#失败
            参数文=str(参数['name'] if 'name' in 参数 else None)+' in '+自身.renderType(约束,引用)#K in
            名类型节点=节点['nameType'] if 'nameType' in 节点 else None#as 目标
            名类型='' if 名类型节点 is None else ' as '+自身.renderType(名类型节点,引用)#as
            值节点=节点['value'] if 'value' in 节点 else None#值类型
            值='unknown' if 值节点 is None else 自身.renderType(值节点,引用)#值
            return '{ '+只读前+'['+参数文+名类型+']'+可选后+': '+值+' }'#映射
        if 种类=='template-literal':#模板
            跨=''.join('${'+自身.renderType(段['type'] if 'type' in 段 else None,引用)+'}'+转义模板(段['text'] if 'text' in 段 else '') for 段 in (节点['spans'] if 'spans' in 节点 else []))#跨
            return '`'+转义模板(节点['head'] if 'head' in 节点 else '')+跨+'`'#模板
        if 种类=='type-query':#typeof
            实参=节点['arguments'] if 'arguments' in 节点 else []#实参
            实参文='' if len(实参)==0 else '<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#列表
            return 'typeof '+(节点['expression'] if 'expression' in 节点 else None)+实参文#typeof
        if 种类=='import-type':#import()
            属性值=节点['attributes'] if 'attributes' in 节点 else None#属性
            属性='' if 属性值 is None else ', '+属性值#属性
            导入='import('+引号(节点['module'] if 'module' in 节点 else '')+属性+')'#import
            限定=节点['qualifier'] if 'qualifier' in 节点 else None#限定
            if 限定 is not None:#限定
                导入=导入+'.'+限定#限定
            实参=节点['arguments'] if 'arguments' in 节点 else []#实参
            实参文='' if len(实参)==0 else '<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#列表
            前='typeof ' if ('typeof' in 节点 and 节点['typeof']) else ''#typeof
            return 前+导入+实参文#import
        if 种类=='predicate':#判断
            断言='asserts ' if ('asserts' in 节点 and 节点['asserts']) else ''#asserts
            谓词类型=节点['type'] if 'type' in 节点 else None#目标类型
            谓词参数=节点['parameter'] if 'parameter' in 节点 else None#参数
            if 谓词类型 is None:#无目标
                return 断言+谓词参数#仅参数
            return 断言+谓词参数+' is '+自身.renderType(谓词类型,引用)#is
        if 种类=='this':#this
            return 'this'#this
        raise 类型图渲染错误('unsupported model variant '+repr(节点))#未覆盖

    def renderSignature(自身,签名,引用=None):#渲染签名（含返回类型）
        """头 + : 返回类型。"""
        return 自身.渲染签名头(签名,引用)+': '+自身.renderType(签名['returns'] if 'returns' in 签名 else None,引用)#签名

    def renderMember(自身,成员,源码修饰=False,引用=None):#渲染一条成员
        """单行 TypeScript 成员文本。"""
        if 源码修饰:#要源码修饰
            return 成员['text'] if 'text' in 成员 else None#保留文本
        名=渲染属性名(成员['name'] if 'name' in 成员 else '')#属性名
        可选='?' if ('optional' in 成员 and 成员['optional']) else ''#可选
        只读='readonly ' if ('readonly' in 成员 and 成员['readonly']) else ''#readonly
        抽象='abstract ' if ('abstract' in 成员 and 成员['abstract']) else ''#abstract
        种类=成员['kind']#种类
        if 种类=='property':#属性
            return 抽象+只读+名+可选+': '+自身.renderType(成员['type'] if 'type' in 成员 else None,引用)#属性
        if 种类=='method':#方法
            return 抽象+名+可选+自身.renderSignature(成员['signature'] if 'signature' in 成员 else {},引用)#方法
        if 种类=='getter':#getter
            return 抽象+'get '+名+'(): '+自身.renderType((成员['signature']['returns'] if 'signature' in 成员 and 'returns' in 成员['signature'] else None),引用)#getter
        if 种类=='setter':#setter
            return 抽象+'set '+名+自身.渲染签名头(成员['signature'] if 'signature' in 成员 else {},引用)#setter
        if 种类=='call':#调用签名
            return 自身.renderSignature(成员['signature'] if 'signature' in 成员 else {},引用)#调用
        if 种类=='construct':#构造签名
            return 'new '+自身.renderSignature(成员['signature'] if 'signature' in 成员 else {},引用)#构造
        if 种类=='index':#索引签名
            签名=成员['signature'] if 'signature' in 成员 else {}#签名
            参数=', '.join(自身.渲染形参(项,引用) for 项 in (签名['parameters'] if 'parameters' in 签名 else []))#形参
            return 只读+'['+参数+']: '+自身.renderType(签名['returns'] if 'returns' in 签名 else None,引用)#索引
        raise 类型图渲染错误('unsupported member variant '+repr(成员))#未覆盖

    def 渲染签名头(自身,签名,引用=None):#渲染签名头
        """类型参数+形参。"""
        return (自身.渲染类型参数列表(签名['typeParameters'] if 'typeParameters' in 签名 else [],引用)
            +'('+', '.join(自身.渲染形参(项,引用) for 项 in (签名['parameters'] if 'parameters' in 签名 else []))+')')#头

    def 渲染形参(自身,参数,引用=None):#渲染一个形参
        """rest/名字/可选: 类型 = 初值。"""
        绑定=参数['binding'] if 'binding' in 参数 else None#绑定
        参数名=参数['name'] if 'name' in 参数 else None#名字
        名=渲染属性名(参数名 or '') if 绑定=='identifier' else (参数名 or '')#名字
        初值节点=参数['initializer'] if 'initializer' in 参数 else None#初值
        可选标记=参数['optional'] if 'optional' in 参数 else None#可选
        剩余=参数['rest'] if 'rest' in 参数 else None#rest
        可选='?' if 初值节点 is None and 可选标记 and not 剩余 else ''#可选
        初值='' if 初值节点 is None else ' = '+初值节点#初值
        rest='...' if 剩余 else ''#rest
        return rest+名+可选+': '+自身.renderType(参数['type'] if 'type' in 参数 else None,引用)+初值#形参

    def 渲染类型参数列表(自身,参数列表,引用=None):#渲染类型参数列表
        """无则空串。"""
        if len(参数列表)==0:#无
            return ''#空
        return '<'+', '.join(自身.渲染类型参数(项,True,引用) for 项 in 参数列表)+'>'#列表

    def 渲染类型参数(自身,参数,含缺省,引用=None):#渲染一个类型参数
        """const/方差/名字/约束/缺省。"""
        方差=参数['variance'] if 'variance' in 参数 else None#方差
        方差前='' if 方差 is None else (('in out' if 方差=='in-out' else 方差)+' ')#修饰
        常量='const ' if ('const' in 参数 and 参数['const']) else ''#const
        约束节点=参数['constraint'] if 'constraint' in 参数 else None#约束
        约束='' if 约束节点 is None else ' extends '+自身.renderType(约束节点,引用)#约束
        缺省节点=参数['default'] if 'default' in 参数 else None#缺省
        缺省='' if (not 含缺省 or 缺省节点 is None) else ' = '+自身.renderType(缺省节点,引用)#缺省
        return 常量+方差前+(参数['name'] if 'name' in 参数 else None)+约束+缺省#参数

    def 渲染对象(自身,成员列表,引用=None):#渲染对象类型字面量
        """空对象 {}。"""
        if len(成员列表)==0:#空
            return '{}'#空
        return '{ '+'; '.join(自身.renderMember(项,False,引用)+';' for 项 in 成员列表)+' }'#成员

    def 索引参数(自身,参数列表):#把类型参数 id 映到源码名
        """id → name。"""
        for 参数 in 参数列表:#每个
            自身.参数名[参数['id']]=参数['name'] if 'name' in 参数 else None#登记

    def renderDeclaration(自身,标识):#渲染一条具名声明
        """导出的 TypeScript 声明文本，不含 JSDoc。"""
        声明=自身.declaration(标识)#取出声明
        参数=自身.渲染类型参数列表(声明['typeParameters'] if 'typeParameters' in 声明 else [])#声明级类型参数
        种类=声明['kind']#声明种类
        if 种类=='enum':#枚举
            成员行=[]#成员行
            for 成员 in 声明['enumMembers'] if 'enumMembers' in 声明 else []:#逐枚举成员
                成员初值=成员['initializer'] if 'initializer' in 成员 else None#可选初值
                初值='' if 成员初值 is None else ' = '+成员初值#可选初值
                成员行.append('    '+渲染属性名(成员['name'] if 'name' in 成员 else '')+初值+',')#名字与初值
            return '\n'.join(['export enum '+声明['name']+' {']+成员行+['}'])#拼成 export enum
        if 种类=='alias':#类型别名
            别名类型=声明['type'] if 'type' in 声明 else None#别名目标
            if 别名类型 is None:#别名必须有类型节点
                raise 类型图渲染错误('alias '+str(标识)+' has no type node')#失败
            return 'export type '+声明['name']+参数+' = '+自身.renderType(别名类型)+';'#export type
        扩展=', '.join(自身.renderType(项) for 项 in (声明['extends'] if 'extends' in 声明 else []))#基类
        实现=', '.join(自身.renderType(项) for 项 in (声明['implements'] if 'implements' in 声明 else []))#接口
        继承=(' extends '+扩展 if 扩展 else '')+(' implements '+实现 if 实现 else '')#heritage
        前='abstract ' if 种类=='class' and ('abstract' in 声明 and 声明['abstract']) else ''#抽象类前缀
        成员行=['    '+自身.renderMember(成员)+';' for 成员 in (声明['members'] if 'members' in 声明 else [])]#缩进成员
        return '\n'.join(['export '+前+种类+' '+声明['name']+参数+继承+' {']+成员行+['}'])#拼成 class/interface

    def 收集成员声明闭包(自身,成员标识列表):#从成员出发的声明闭包
        """按图序的声明；不含隐式无根。"""
        return 自身.声明闭包(成员标识列表,[])#类型根为空

    def 收集类型声明闭包(自身,类型标识列表):#从类型根出发的声明闭包
        """按图序的声明。"""
        return 自身.声明闭包([],类型标识列表)#成员 id 为空

    def 声明闭包(自身,成员标识列表,类型标识列表):#从成员与类型根收集传递闭包
        """图序声明，去重。"""
        已收录=set()#已收录的声明
        访问中=set()#正在访问、用于破环

        def 访问节点(标识):#递归访问类型节点
            """递归访问类型节点。"""
            节点=自身.node(标识)#取出节点
            种类=节点['kind']#种类
            目标=节点['target'] if 'target' in 节点 else None#目标
            if 种类=='reference' and 目标 is not None and 'kind' in 目标 and 目标['kind']=='declaration':#引用声明
                访问声明(目标['symbol'])#跟过去
            if 种类=='import-type':#import 目标
                if 目标 is not None and ('kind' in 目标) and 目标['kind']=='declaration':#是声明
                    访问声明(目标['symbol'] if 'symbol' in 目标 else None)#跟过去
            for 子 in 子类型节点标识列表(节点):#子类型边
                访问节点(子)#递归
            for 签名 in 收集节点签名(节点):#函数/构造签名
                访问签名(签名)#签名
            if 种类=='object':#对象成员
                for 成员 in 节点['members'] if 'members' in 节点 else []:#成员
                    访问成员(成员)#成员图

        def 访问签名(签名):#访问一条签名
            """访问一条签名。"""
            for 参数 in 签名['typeParameters'] if 'typeParameters' in 签名 else []:#类型参数
                约束=参数['constraint'] if 'constraint' in 参数 else None#约束
                if 约束 is not None:#约束
                    访问节点(约束)#约束类型
                缺省=参数['default'] if 'default' in 参数 else None#缺省
                if 缺省 is not None:#缺省
                    访问节点(缺省)#缺省类型
            for 参数 in 签名['parameters'] if 'parameters' in 签名 else []:#形参
                访问节点(参数['type'] if 'type' in 参数 else None)#形参类型
            访问节点(签名['returns'] if 'returns' in 签名 else None)#返回类型

        def 访问成员(成员):#访问一条成员
            """访问一条成员。"""
            if 成员['kind']=='property':#属性
                访问节点(成员['type'] if 'type' in 成员 else None)#类型节点
            else:#其余走签名
                访问签名(成员['signature'] if 'signature' in 成员 else {})#签名

        def 访问声明(标识):#访问一条声明（破环）
            """访问一条声明（破环）。"""
            if 标识 in 已收录 or 标识 in 访问中:#已收录或正在访问
                return#跳过
            访问中.add(标识)#标为正在访问
            声明=自身.declaration(标识)#取出声明
            for 参数 in 声明['typeParameters'] if 'typeParameters' in 声明 else []:#声明级类型参数
                约束=参数['constraint'] if 'constraint' in 参数 else None#约束
                if 约束 is not None:#约束
                    访问节点(约束)#约束
                缺省=参数['default'] if 'default' in 参数 else None#缺省
                if 缺省 is not None:#缺省
                    访问节点(缺省)#缺省
            for 类型 in list(声明['extends'] if 'extends' in 声明 else [])+list(声明['implements'] if 'implements' in 声明 else []):#heritage
                访问节点(类型)#heritage 类型
            别名类型=声明['type'] if 'type' in 声明 else None#别名目标
            if 别名类型 is not None:#别名目标
                访问节点(别名类型)#目标类型
            for 成员 in 声明['members'] if 'members' in 声明 else []:#声明成员
                访问成员(成员)#成员
            访问中.discard(标识)#结束访问
            已收录.add(标识)#收录

        for 标识 in 成员标识列表:#从成员根出发
            访问成员(自身.member(标识))#成员
        for 标识 in 类型标识列表:#从类型根出发
            访问节点(标识)#节点
        return [声明 for 声明 in (自身.graph['declarations'] if 'declarations' in 自身.graph else []) if 声明['id'] in 已收录]#按图序过滤

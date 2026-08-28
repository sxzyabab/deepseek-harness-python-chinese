"""对与编译器无关的 TypeGraph 做渲染与遍历。

对齐上游 `typert/generator/src/renderer.ts`。公开面仅中文名。
发射器走本模块，不回头碰 TypeScript AST。
"""
from .模型 import 子类型节点标识们,取字段#子边与读字段

__all__=[#仅中文公开名
    '类型图渲染错误','类型图渲染器','TypeGraphRenderError','TypeGraphRenderer',
]#公开面结束

class 类型图渲染错误(Exception):#类型图渲染错误
    """渲染或遍历内部不一致的 TypeGraph 时失败。"""
    name='TypeGraphRenderError'#错误名

TypeGraphRenderError=类型图渲染错误#上游名

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
    import re#正则
    if re.match(r'^(?:[$A-Z_a-z][$\w]*|\d+)$',名):#合法
        return 名#原样
    return 引号(名)#加引号

def 需要数组括号(节点):#数组元素是否需要括号
    """联合/函数等后缀 [] 会歧义。"""
    return 取字段(节点,'kind') in ('union','intersection','function','constructor','conditional')#需括号

def 节点签名们(节点):#节点自带的签名
    """函数与构造各一条。"""
    return [取字段(节点,'signature')] if 取字段(节点,'kind') in ('function','constructor') else []#签名

class 类型图渲染器:#类型图渲染器
    """在没有编译器对象的情况下读取并渲染一张 TypeGraph。"""
    def __init__(自身,图):#按完整图建索引
        """保留原图并建查找表。"""
        自身.graph=图#原图
        自身.节点们={取字段(节点,'id'):节点 for 节点 in (取字段(图,'nodes') or [])}#节点表
        自身.声明们={取字段(声明,'id'):声明 for 声明 in (取字段(图,'declarations') or [])}#声明表
        自身.成员们={}#成员表
        for 声明 in 取字段(图,'declarations') or []:#跨声明
            for 成员 in 取字段(声明,'members') or []:#成员
                自身.成员们[取字段(成员,'id')]=成员#登记
        自身.参数名={}#类型参数 id → 源码名
        for 声明 in 取字段(图,'declarations') or []:#逐声明
            自身.索引参数(取字段(声明,'typeParameters') or [])#声明级
            for 成员 in 取字段(声明,'members') or []:#成员级
                if 'signature' in 成员 or 取字段(成员,'signature') is not None:#有签名
                    签名=取字段(成员,'signature') or {}#签名
                    自身.索引参数(取字段(签名,'typeParameters') or [])#签名级

    def node(自身,标识):#按 id 取类型节点
        """缺节点即断边。"""
        节点=自身.节点们.get(标识)#查找
        if 节点 is None:#缺
            raise 类型图渲染错误('type graph references missing node '+str(标识))#断边
        return 节点#命中

    def declaration(自身,标识):#按符号 id 取声明
        """缺声明即断边。"""
        声明=自身.声明们.get(标识)#查找
        if 声明 is None:#缺
            raise 类型图渲染错误('type graph references missing declaration '+str(标识))#断边
        return 声明#命中

    def member(自身,标识):#按成员 id 取成员
        """缺成员即断边。"""
        成员=自身.成员们.get(标识)#查找
        if 成员 is None:#缺
            raise 类型图渲染错误('type graph references missing member '+str(标识))#断边
        return 成员#命中

    def renderType(自身,标识,引用=None):#渲染一条类型表达式
        """按种类分发。"""
        节点=自身.node(标识)#取出
        种类=取字段(节点,'kind')#种类
        if 种类=='keyword':#关键字
            return 取字段(节点,'name')#名字
        if 种类=='literal':#字面量
            return 取字段(节点,'text')#文本
        if 种类=='parenthesized':#括号
            return '('+自身.renderType(取字段(节点,'type'),引用)+')'#包一层
        if 种类=='reference':#具名引用
            目标=取字段(节点,'target') or {}#目标
            if 取字段(目标,'kind')=='type-parameter':#类型参数
                名=自身.参数名.get(取字段(目标,'parameter'),取字段(节点,'name'))#参数名
            elif 取字段(目标,'kind')=='declaration':#声明
                名=(引用 or {}).get(取字段(目标,'symbol'),取字段(节点,'name')) if isinstance(引用,dict) else 取字段(节点,'name')#生成名
            else:#其它
                名=取字段(节点,'name')#源名
            实参=取字段(节点,'arguments') or []#实参
            if len(实参)==0:#无实参
                return 名#裸名
            return 名+'<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#带实参
        if 种类=='union':#联合
            return ' | '.join(自身.renderType(项,引用) for 项 in (取字段(节点,'types') or []))#|
        if 种类=='intersection':#交叉
            return ' & '.join(自身.renderType(项,引用) for 项 in (取字段(节点,'types') or []))#&
        if 种类=='array':#数组
            元素=自身.renderType(取字段(节点,'element'),引用)#元素
            包='('+元素+')' if 需要数组括号(自身.node(取字段(节点,'element'))) else 元素#括号
            return 包+'[]'#后缀
        if 种类=='tuple':#元组
            元素们=[]#文本
            for 元素 in 取字段(节点,'elements') or []:#逐元素
                类型=自身.renderType(取字段(元素,'type'),引用)#类型
                名=取字段(元素,'name')#名字
                rest='...' if 取字段(元素,'rest') else ''#rest
                可选='?' if 取字段(元素,'optional') else ''#可选
                if 名 is not None:#具名
                    元素们.append(rest+名+可选+': '+类型)#具名
                else:#匿名
                    元素们.append(rest+类型+可选)#匿名
            return '['+', '.join(元素们)+']'#元组
        if 种类=='object':#对象
            return 自身.渲染对象(取字段(节点,'members') or [],引用)#对象
        if 种类=='function':#函数
            签名=取字段(节点,'signature') or {}#签名
            return 自身.渲染签名头(签名,引用)+' => '+自身.renderType(取字段(签名,'returns'),引用)#函数
        if 种类=='constructor':#构造
            签名=取字段(节点,'signature') or {}#签名
            前='abstract ' if 取字段(节点,'abstract') else ''#abstract
            return 前+'new '+自身.渲染签名头(签名,引用)+' => '+自身.renderType(取字段(签名,'returns'),引用)#构造
        if 种类=='indexed-access':#索引访问
            return 自身.renderType(取字段(节点,'object'),引用)+'['+自身.renderType(取字段(节点,'index'),引用)+']'#索引
        if 种类=='operator':#运算符
            return 取字段(节点,'operator')+' '+自身.renderType(取字段(节点,'type'),引用)#运算符
        if 种类=='conditional':#条件
            return (自身.renderType(取字段(节点,'check'),引用)+' extends '+自身.renderType(取字段(节点,'extends'),引用)
                +' ? '+自身.renderType(取字段(节点,'whenTrue'),引用)+' : '+自身.renderType(取字段(节点,'whenFalse'),引用))#条件
        if 种类=='infer':#infer
            return 'infer '+自身.渲染类型参数(取字段(节点,'parameter') or {},False,引用)#infer
        if 种类=='mapped':#映射
            只读=取字段(节点,'readonly')#readonly
            只读前='' if 只读=='preserve' else ('-readonly ' if 只读=='remove' else 'readonly ')#修饰
            可选=取字段(节点,'optional')#optional
            可选后='' if 可选=='preserve' else ('-?' if 可选=='remove' else '?')#修饰
            参数=取字段(节点,'parameter') or {}#参数
            if 取字段(参数,'constraint') is None:#无约束
                raise 类型图渲染错误('mapped type parameter '+str(取字段(参数,'name'))+' has no constraint')#失败
            参数文=取字段(参数,'name')+' in '+自身.renderType(取字段(参数,'constraint'),引用)#K in
            名类型='' if 取字段(节点,'nameType') is None else ' as '+自身.renderType(取字段(节点,'nameType'),引用)#as
            值='unknown' if 取字段(节点,'value') is None else 自身.renderType(取字段(节点,'value'),引用)#值
            return '{ '+只读前+'['+参数文+名类型+']'+可选后+': '+值+' }'#映射
        if 种类=='template-literal':#模板
            跨=''.join('${'+自身.renderType(取字段(段,'type'),引用)+'}'+转义模板(取字段(段,'text') or '') for 段 in (取字段(节点,'spans') or []))#跨
            return '`'+转义模板(取字段(节点,'head') or '')+跨+'`'#模板
        if 种类=='type-query':#typeof
            实参=取字段(节点,'arguments') or []#实参
            实参文='' if len(实参)==0 else '<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#列表
            return 'typeof '+取字段(节点,'expression')+实参文#typeof
        if 种类=='import-type':#import()
            属性='' if 取字段(节点,'attributes') is None else ', '+取字段(节点,'attributes')#属性
            导入='import('+引号(取字段(节点,'module') or '')+属性+')'#import
            if 取字段(节点,'qualifier') is not None:#限定
                导入=导入+'.'+取字段(节点,'qualifier')#限定
            实参=取字段(节点,'arguments') or []#实参
            实参文='' if len(实参)==0 else '<'+', '.join(自身.renderType(项,引用) for 项 in 实参)+'>'#列表
            前='typeof ' if 取字段(节点,'typeof') else ''#typeof
            return 前+导入+实参文#import
        if 种类=='predicate':#判断
            断言='asserts ' if 取字段(节点,'asserts') else ''#asserts
            if 取字段(节点,'type') is None:#无目标
                return 断言+取字段(节点,'parameter')#仅参数
            return 断言+取字段(节点,'parameter')+' is '+自身.renderType(取字段(节点,'type'),引用)#is
        if 种类=='this':#this
            return 'this'#this
        raise 类型图渲染错误('unsupported model variant '+repr(节点))#未覆盖

    def renderSignature(自身,签名,引用=None):#渲染签名（含返回类型）
        """头 + : 返回类型。"""
        return 自身.渲染签名头(签名,引用)+': '+自身.renderType(取字段(签名,'returns'),引用)#签名

    def renderMember(自身,成员,源码修饰=False,引用=None):#渲染一条成员
        """单行 TypeScript 成员文本。"""
        if 源码修饰:#要源码修饰
            return 取字段(成员,'text')#保留文本
        名=渲染属性名(取字段(成员,'name') or '')#属性名
        可选='?' if 取字段(成员,'optional') else ''#可选
        只读='readonly ' if 取字段(成员,'readonly') else ''#readonly
        抽象='abstract ' if 取字段(成员,'abstract') else ''#abstract
        种类=取字段(成员,'kind')#种类
        if 种类=='property':#属性
            return 抽象+只读+名+可选+': '+自身.renderType(取字段(成员,'type'),引用)#属性
        if 种类=='method':#方法
            return 抽象+名+可选+自身.renderSignature(取字段(成员,'signature') or {},引用)#方法
        if 种类=='getter':#getter
            return 抽象+'get '+名+'(): '+自身.renderType(取字段(取字段(成员,'signature'),'returns'),引用)#getter
        if 种类=='setter':#setter
            return 抽象+'set '+名+自身.渲染签名头(取字段(成员,'signature') or {},引用)#setter
        if 种类=='call':#调用签名
            return 自身.renderSignature(取字段(成员,'signature') or {},引用)#调用
        if 种类=='construct':#构造签名
            return 'new '+自身.renderSignature(取字段(成员,'signature') or {},引用)#构造
        if 种类=='index':#索引签名
            签名=取字段(成员,'signature') or {}#签名
            参数=', '.join(自身.渲染形参(项,引用) for 项 in (取字段(签名,'parameters') or []))#形参
            return 只读+'['+参数+']: '+自身.renderType(取字段(签名,'returns'),引用)#索引
        raise 类型图渲染错误('unsupported member variant '+repr(成员))#未覆盖

    def 渲染签名头(自身,签名,引用=None):#渲染签名头
        """类型参数+形参。"""
        return (自身.渲染类型参数列表(取字段(签名,'typeParameters') or [],引用)
            +'('+', '.join(自身.渲染形参(项,引用) for 项 in (取字段(签名,'parameters') or []))+')')#头

    def 渲染形参(自身,参数,引用=None):#渲染一个形参
        """rest/名字/可选: 类型 = 初值。"""
        绑定=取字段(参数,'binding')#绑定
        名=渲染属性名(取字段(参数,'name') or '') if 绑定=='identifier' else (取字段(参数,'name') or '')#名字
        可选='?' if 取字段(参数,'initializer') is None and 取字段(参数,'optional') and not 取字段(参数,'rest') else ''#可选
        初值='' if 取字段(参数,'initializer') is None else ' = '+取字段(参数,'initializer')#初值
        rest='...' if 取字段(参数,'rest') else ''#rest
        return rest+名+可选+': '+自身.renderType(取字段(参数,'type'),引用)+初值#形参

    def 渲染类型参数列表(自身,参数们,引用=None):#渲染类型参数列表
        """无则空串。"""
        if len(参数们)==0:#无
            return ''#空
        return '<'+', '.join(自身.渲染类型参数(项,True,引用) for 项 in 参数们)+'>'#列表

    def 渲染类型参数(自身,参数,含缺省,引用=None):#渲染一个类型参数
        """const/方差/名字/约束/缺省。"""
        方差=取字段(参数,'variance')#方差
        方差前='' if 方差 is None else (('in out' if 方差=='in-out' else 方差)+' ')#修饰
        常量='const ' if 取字段(参数,'const') else ''#const
        约束='' if 取字段(参数,'constraint') is None else ' extends '+自身.renderType(取字段(参数,'constraint'),引用)#约束
        缺省='' if (not 含缺省 or 取字段(参数,'default') is None) else ' = '+自身.renderType(取字段(参数,'default'),引用)#缺省
        return 常量+方差前+取字段(参数,'name')+约束+缺省#参数

    def 渲染对象(自身,成员们,引用=None):#渲染对象类型字面量
        """空对象 {}。"""
        if len(成员们)==0:#空
            return '{}'#空
        return '{ '+'; '.join(自身.renderMember(项,False,引用)+';' for 项 in 成员们)+' }'#成员

    def 索引参数(自身,参数们):#把类型参数 id 映到源码名
        """id → name。"""
        for 参数 in 参数们:#每个
            自身.参数名[取字段(参数,'id')]=取字段(参数,'name')#登记

    def renderDeclaration(自身,标识):#渲染一条具名声明
        """导出的 TypeScript 声明文本，不含 JSDoc。"""
        声明=自身.declaration(标识)#取出声明
        参数=自身.渲染类型参数列表(取字段(声明,'typeParameters') or [])#声明级类型参数
        种类=取字段(声明,'kind')#声明种类
        if 种类=='enum':#枚举
            成员行=[]#成员行
            for 成员 in 取字段(声明,'enumMembers') or []:#逐枚举成员
                初值='' if 取字段(成员,'initializer') is None else ' = '+取字段(成员,'initializer')#可选初值
                成员行.append('    '+渲染属性名(取字段(成员,'name') or '')+初值+',')#名字与初值
            return '\n'.join(['export enum '+取字段(声明,'name')+' {']+成员行+['}'])#拼成 export enum
        if 种类=='alias':#类型别名
            if 取字段(声明,'type') is None:#别名必须有类型节点
                raise 类型图渲染错误('alias '+str(标识)+' has no type node')#失败
            return 'export type '+取字段(声明,'name')+参数+' = '+自身.renderType(取字段(声明,'type'))+';'#export type
        扩展=', '.join(自身.renderType(项) for 项 in (取字段(声明,'extends') or []))#基类
        实现=', '.join(自身.renderType(项) for 项 in (取字段(声明,'implements') or []))#接口
        继承=(' extends '+扩展 if 扩展 else '')+(' implements '+实现 if 实现 else '')#heritage
        前='abstract ' if 种类=='class' and 取字段(声明,'abstract') else ''#抽象类前缀
        成员行=['    '+自身.renderMember(成员)+';' for 成员 in (取字段(声明,'members') or [])]#缩进成员
        return '\n'.join(['export '+前+种类+' '+取字段(声明,'name')+参数+继承+' {']+成员行+['}'])#拼成 class/interface

    def declarationClosureForMembers(自身,成员标识们):#从成员出发的声明闭包
        """按图序的声明；不含隐式无根。"""
        return 自身.声明闭包(成员标识们,[])#类型根为空

    def declarationClosureForTypes(自身,类型标识们):#从类型根出发的声明闭包
        """按图序的声明。"""
        return 自身.声明闭包([],类型标识们)#成员 id 为空

    def 声明闭包(自身,成员标识们,类型标识们):#从成员与类型根收集传递闭包
        """图序声明，去重。"""
        已收录=set()#已收录的声明
        访问中=set()#正在访问、用于破环

        def 访问节点(标识):#递归访问类型节点
            节点=自身.node(标识)#取出节点
            种类=取字段(节点,'kind')#种类
            if 种类=='reference' and 取字段(取字段(节点,'target'),'kind')=='declaration':#引用声明
                访问声明(取字段(取字段(节点,'target'),'symbol'))#跟过去
            if 种类=='import-type':#import 目标
                目标=取字段(节点,'target')#可选目标
                if 目标 is not None and 取字段(目标,'kind')=='declaration':#是声明
                    访问声明(取字段(目标,'symbol'))#跟过去
            for 子 in 子类型节点标识们(节点):#子类型边
                访问节点(子)#递归
            for 签名 in 节点签名们(节点):#函数/构造签名
                访问签名(签名)#签名
            if 种类=='object':#对象成员
                for 成员 in 取字段(节点,'members') or []:#成员
                    访问成员(成员)#成员图

        def 访问签名(签名):#访问一条签名
            for 参数 in 取字段(签名,'typeParameters') or []:#类型参数
                if 取字段(参数,'constraint') is not None:#约束
                    访问节点(取字段(参数,'constraint'))#约束类型
                if 取字段(参数,'default') is not None:#缺省
                    访问节点(取字段(参数,'default'))#缺省类型
            for 参数 in 取字段(签名,'parameters') or []:#形参
                访问节点(取字段(参数,'type'))#形参类型
            访问节点(取字段(签名,'returns'))#返回类型

        def 访问成员(成员):#访问一条成员
            if 取字段(成员,'kind')=='property':#属性
                访问节点(取字段(成员,'type'))#类型节点
            else:#其余走签名
                访问签名(取字段(成员,'signature') or {})#签名

        def 访问声明(标识):#访问一条声明（破环）
            if 标识 in 已收录 or 标识 in 访问中:#已收录或正在访问
                return#跳过
            访问中.add(标识)#标为正在访问
            声明=自身.declaration(标识)#取出声明
            for 参数 in 取字段(声明,'typeParameters') or []:#声明级类型参数
                if 取字段(参数,'constraint') is not None:#约束
                    访问节点(取字段(参数,'constraint'))#约束
                if 取字段(参数,'default') is not None:#缺省
                    访问节点(取字段(参数,'default'))#缺省
            for 类型 in list(取字段(声明,'extends') or [])+list(取字段(声明,'implements') or []):#heritage
                访问节点(类型)#heritage 类型
            if 取字段(声明,'type') is not None:#别名目标
                访问节点(取字段(声明,'type'))#目标类型
            for 成员 in 取字段(声明,'members') or []:#声明成员
                访问成员(成员)#成员
            访问中.discard(标识)#结束访问
            已收录.add(标识)#收录

        for 标识 in 成员标识们:#从成员根出发
            访问成员(自身.member(标识))#成员
        for 标识 in 类型标识们:#从类型根出发
            访问节点(标识)#节点
        return [声明 for 声明 in (取字段(自身.graph,'declarations') or []) if 取字段(声明,'id') in 已收录]#按图序过滤

TypeGraphRenderer=类型图渲染器#上游名

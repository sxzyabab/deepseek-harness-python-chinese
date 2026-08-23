"""Meta 校验按工作流元数据约定检查调用方提供的数据，并按名称拒绝每一条违规。Meta 作为已做模式检查的 JSON 数据到达，绝不是被求值的脚本文本；在宿主上求值它可能在 worker 超时之外运行 getter，而该超时正是为了隔离模型写的代码。"""
from ..工作流 import 工作流错误#导入工作流错误

def 校验元数据形态(元数据):#校验 meta 形态并收集违规
    """收集一份 meta 值的形态违规（按缝约定是普通 JSON 数据）。返回 {meta?, violations}。"""
    违规=[]#违规列表
    if not isinstance(元数据,dict) or 元数据 is None:#不是普通对象
        return {'violations':['meta must be an object']}#整块不是对象
    记录=元数据#按字段表查看
    已知=set(['name','description','whenToUse','phases'])#允许的字段名
    for 键 in 记录.keys():#检查未知字段
        if 键 not in 已知:#未知字段
            违规.append('meta.'+键+' is not a recognized field (name/description/whenToUse/phases)')#未知字段记一条
    名称值=记录.get('name')#取出名称
    if not isinstance(名称值,str) or len(名称值)==0:#名称必须非空字符串
        违规.append('meta.name must be a non-empty string')#名称违规
    描述值=记录.get('description')#取出描述
    if not isinstance(描述值,str) or len(描述值)==0:#描述必须非空字符串
        违规.append('meta.description must be a non-empty string')#描述违规
    if 'whenToUse' in 记录 and not isinstance(记录.get('whenToUse'),str):#适用场景若出现必须是字符串
        违规.append('meta.whenToUse must be a string')#适用场景违规
    阶段列表=[]#规范化后的阶段列表
    if 'phases' in 记录:#出现了 phases
        原始阶段=记录.get('phases')#取出阶段
        if not isinstance(原始阶段,list):#不是数组
            违规.append('meta.phases must be an array')#阶段必须是数组
        else:#逐项检查阶段
            for 索引,阶段 in enumerate(原始阶段):#校验每一个阶段项
                if not isinstance(阶段,dict) or 阶段 is None:#项不是普通对象
                    违规.append('meta.phases['+str(索引)+'] must be an object')#记形态违规
                    continue#该项无法继续
                项=阶段#按字段表查看该项
                for 键 in 项.keys():#检查未知阶段字段
                    if 键 not in ('title','detail','provider','model'):#未知字段
                        违规.append('meta.phases['+str(索引)+'].'+键+' is not a recognized field')#未知字段
                标题=项.get('title')#取出标题
                if not isinstance(标题,str) or len(标题)==0:#标题必须非空
                    违规.append('meta.phases['+str(索引)+'].title must be a non-empty string')#标题违规
                if 'detail' in 项 and not isinstance(项.get('detail'),str):#细节若出现必须是字符串
                    违规.append('meta.phases['+str(索引)+'].detail must be a string')#细节违规
                if 'provider' in 项 and not isinstance(项.get('provider'),str):#提供方若出现必须是字符串
                    违规.append('meta.phases['+str(索引)+'].provider must be a string')#提供方违规
                if 'model' in 项 and not isinstance(项.get('model'),str):#模型若出现必须是字符串
                    违规.append('meta.phases['+str(索引)+'].model must be a string')#模型违规
                if len(违规)==0:#至此该项无违规才收入规范化副本
                    规范化={'title':标题}#组装规范化阶段
                    if 'detail' in 项:#可选细节
                        规范化['detail']=项['detail']#写入细节
                    if 'provider' in 项:#可选提供方
                        规范化['provider']=项['provider']#写入提供方
                    if 'model' in 项:#可选模型
                        规范化['model']=项['model']#写入模型
                    阶段列表.append(规范化)#收入列表
    if len(违规)>0:#有违规则不返回 meta
        return {'violations':违规}#只返回违规
    结果={'name':记录['name'],'description':记录['description']}#规范化 meta
    if 'whenToUse' in 记录:#可选适用场景
        结果['whenToUse']=记录['whenToUse']#写入
    if 'phases' in 记录:#可选阶段
        结果['phases']=阶段列表#写入
    return {'violations':[],'meta':结果}#形态合法，返回规范化副本

def 校验元数据(值):#校验并规范化 meta
    """按工作流元数据约定校验调用方提供的 meta 值。抛出 META_INVALID 并点名每一条违规（未知字段、缺失/类型错误的 name/description、畸形 phases）；返回的 meta 是由已校验字段建成的规范化副本，因此引擎从不与调用方对象共享别名。"""
    形态=校验元数据形态(值)#先收集形态结果
    if 形态.get('meta') is None:#有违规
        raise 工作流错误('invalid meta: '+'; '.join(形态['violations']),'META_INVALID')#点名全部违规
    return 形态['meta']#返回规范化副本

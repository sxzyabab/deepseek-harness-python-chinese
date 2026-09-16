"""按工作流元数据合同校验调用方提供的 DATA，按名拒绝每一处违规。元数据作为模式已检查的 JSON 数据到达，从不求值脚本文本。"""
from ..工作流 import 工作流错误#缝上错误

__all__=['校验元数据']#仅中文公开名

已知元数据键=frozenset(('name','description','whenToUse','phases'))#允许字段
已知阶段键=frozenset(('title','detail','provider','model'))#阶段允许字段

def 校验元数据形态(元数据):#收集形态违规
    """收集一个元数据值的形态违规（按缝约定是普通 JSON 数据）。返回 {meta?, violations}。"""
    违规=[]#违规表
    if type(元数据) is not dict:#必须对象
        return {'violations':['meta must be an object']}#不是对象
    for 键 in 元数据.keys():#未知字段
        if 键 not in 已知元数据键:#不认识
            违规.append('meta.'+键+' is not a recognized field (name/description/whenToUse/phases)')#未知
    名=元数据['name'] if 'name' in 元数据 else None#名称
    if type(名) is not str or len(名)==0:#必须非空串
        违规.append('meta.name must be a non-empty string')#名称
    描述=元数据['description'] if 'description' in 元数据 else None#描述
    if type(描述) is not str or len(描述)==0:#必须非空串
        违规.append('meta.description must be a non-empty string')#描述
    if 'whenToUse' in 元数据 and 元数据['whenToUse'] is not None and type(元数据['whenToUse']) is not str:#可选串
        违规.append('meta.whenToUse must be a string')#类型
    阶段表=[]#规范化阶段
    if 'phases' in 元数据 and 元数据['phases'] is not None:#有阶段
        阶段值=元数据['phases']#取出
        if type(阶段值) is not list:#必须数组
            违规.append('meta.phases must be an array')#类型
        else:#逐项
            下标=0#从 0
            while 下标<len(阶段值):#逐个
                阶段=阶段值[下标]#一项
                if type(阶段) is not dict:#必须对象
                    违规.append('meta.phases['+str(下标)+'] must be an object')#类型
                    下标+=1#推进
                    continue#下一项
                for 键 in 阶段.keys():#未知字段
                    if 键 not in 已知阶段键:#不认识
                        违规.append('meta.phases['+str(下标)+'].'+键+' is not a recognized field')#未知
                标题=阶段['title'] if 'title' in 阶段 else None#标题
                if type(标题) is not str or len(标题)==0:#必须非空串
                    违规.append('meta.phases['+str(下标)+'].title must be a non-empty string')#标题
                if 'detail' in 阶段 and 阶段['detail'] is not None and type(阶段['detail']) is not str:#可选串
                    违规.append('meta.phases['+str(下标)+'].detail must be a string')#细节
                if 'provider' in 阶段 and 阶段['provider'] is not None and type(阶段['provider']) is not str:#可选串
                    违规.append('meta.phases['+str(下标)+'].provider must be a string')#提供方
                if 'model' in 阶段 and 阶段['model'] is not None and type(阶段['model']) is not str:#可选串
                    违规.append('meta.phases['+str(下标)+'].model must be a string')#模型
                if len(违规)==0:#尚无违规才收下
                    一条={'title':标题}#标题
                    if 'detail' in 阶段 and 阶段['detail'] is not None:#有细节
                        一条['detail']=阶段['detail']#带上
                    if 'provider' in 阶段 and 阶段['provider'] is not None:#有提供方
                        一条['provider']=阶段['provider']#带上
                    if 'model' in 阶段 and 阶段['model'] is not None:#有模型
                        一条['model']=阶段['model']#带上
                    阶段表.append(一条)#收下
                下标+=1#推进
    if len(违规)>0:#有违规
        return {'violations':违规}#只返回违规
    规范化={'name':名,'description':描述}#必填
    if 'whenToUse' in 元数据 and 元数据['whenToUse'] is not None:#有适用
        规范化['whenToUse']=元数据['whenToUse']#带上
    if 'phases' in 元数据 and 元数据['phases'] is not None:#有阶段
        规范化['phases']=阶段表#带上
    return {'violations':违规,'meta':规范化}#通过

def 校验元数据(值):#校验并规范化
    """按工作流元数据合同校验调用方元数据。抛出 META_INVALID 并点名每一处违规；返回由已校验字段建成的规范化拷贝，引擎从不别名调用方对象。"""
    结果=校验元数据形态(值)#形态
    if 'meta' not in 结果:#失败
        raise 工作流错误('invalid meta: '+'; '.join(结果['violations']),'META_INVALID')#无效
    return 结果['meta']#规范化拷贝

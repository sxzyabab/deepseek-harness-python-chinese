"""Windows ACL 工作区与私有临时能力的规范目录边界检查。"""
import os#路径与realpath

def 包含目录(根,候选):#根是否包含候选目录
    """`根` 是否与 `候选` 为同一规范目录，或包含它。"""
    规范根=os.path.realpath(根)#规范根
    规范候选=os.path.realpath(候选)#规范候选
    相对=os.path.relpath(规范候选,规范根)#两规范路径的相对关系
    if 相对=='.':#同目录
        return True#包含
    if os.path.isabs(相对):#绝对相对表示跨盘
        return False#不包含
    if 相对=='..' or 相对.startswith('..'+os.sep):#越出
        return False#不包含
    return True#相对下降且未越出

def 断言临时根在工作区外(工作区根,临时根):#断言临时根在工作区外
    """拒绝位于工作区内的临时父目录：其下创建的每个子目录都会继承常驻工作区能力。"""
    if 包含目录(工作区根,临时根):#临时根落在工作区内
        raise Exception('Windows ACL temp root must be outside the workspace: workspace='+工作区根+'; temp='+临时根)#拒绝重叠

def 断言私有临时不相交(可写目录们,临时目录):#断言私有临时与可写目录不相交
    """拒绝实际私有临时目录与任一可写目录重叠：任一方向的继承都会把两种能力合并。"""
    for 可写目录 in 可写目录们:#逐个可写目录
        if 包含目录(可写目录,临时目录) or 包含目录(临时目录,可写目录):#任一方向包含
            raise Exception('AclSandbox private temp directory must be disjoint from writable directories: writable='+可写目录+'; temp='+临时目录)#拒绝重叠

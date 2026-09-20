from ..镜像布局 import 默认根

__all__=['dsh根','dsh主目录','dsh节点模块','dsh配置','dsh工作区','dsh临时']

dsh根=默认根#虚拟文件系统根；process.cwd()与每个绝对路径从此开始
dsh主目录=f'{dsh根}/home'#镜像内的持久状态目录
dsh节点模块=f'{dsh根}/node_modules'#由worker模块加载器解析的扁平、无符号链接包树
dsh配置=f'{dsh根}/config'#存放合成cordis.yml与智能体预设树的目录
dsh工作区=f'{dsh根}/workspace'#默认（空）工作区目录
dsh临时=f'{dsh根}/tmp'#os.tmpdir()报告的临时目录

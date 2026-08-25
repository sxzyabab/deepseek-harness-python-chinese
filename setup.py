from __future__ import annotations
from pathlib import Path
import shutil
from setuptools import setup as 安装
from setuptools.command.build_py import build_py

根包名='pydsh'

根目录=Path(__file__).resolve().parent
源码目录=根目录/"源码"
依赖目录=根目录/"依赖快照"

if not 源码目录.is_dir():
    raise RuntimeError("源码目录不存在")
if not 依赖目录.is_dir():
    raise RuntimeError("依赖快照目录不存在")

def 复制文件树(源:Path,目标:Path)->None:
    if 目标.exists():
        shutil.rmtree(目标)
    if 源.is_dir():
        目标.mkdir(parents=True,exist_ok=True)
        #子文件夹与文件
        for 源_ in 源.iterdir():
            if 源_.name=="__pycache__":#跳过pycache
                continue
            目标_=目标/源_.name
            复制文件树(源_,目标_)
    else:#单文件直接复制
        目标.write_bytes(源.read_bytes())

class 安装指令(build_py):
    def run(self):
        shutil.copytree(
            根目录,
            Path(self.build_lib)/根包名,
            ignore=shutil.ignore_patterns(
                'build','*.egg-info','__pycache__','.git'
                ),dirs_exist_ok=True
            )
        复制文件树(根目录/'.git',Path(self.build_lib)/根包名/".git")

安装(
    name=根包名,
    packages=[根包名],
    cmdclass={"build_py":安装指令},
)

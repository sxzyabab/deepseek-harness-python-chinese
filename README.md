# Deepseek Harness Python (中文学习版)

**此仓库非官方仓库**（ 官方仓库: [https://github.com/deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) ）

此仓库为官方deepseek harness的python版，大部分代码由**AI翻译**，并由**人工润色**

为了便于研究，该仓库采用全中文设计，**部分内容有删改**，需要原文请至官方仓库寻找

该仓库目前无法直接运行，在之后的版本会修复

## 使用

安装为python库：
```shell
git clone https://github.com/sxzyabab/deepseek-harness-python-chinese.git
cd deepseek-harness-python-chinese
pip install .
```
>注：目前只是能安装还不能正常导入

或下载源码后直接导入(使用`importlib`或改名为不含`-`的名称后导入)

## 文件导览

[文档](文档/)/
    [官方文档](文档/官方文档/)

[依赖快照](依赖快照/)/ #原vendor
    [cordis](依赖快照/cordis/)
    [loader](依赖快照/loader/)
    [cosmokit.py](依赖快照/cosmokit.py)
    [hmr.py](依赖快照/hmr.py)
    [include.py](依赖快照/include.py)
    [logger_console.py](依赖快照/logger_console.py)
    [schemastery.py](依赖快照/schemastery.py)
    [timer.py](依赖快照/timer.py)

[源码](源码)/ #原package

[css](css)/ #从插件内提取出的css(原版)

注:
    1.部分包尚未完成
    2.示例尚未迁移
    3.部分外围内容(官方开发用脚本等非核心代码)不加入
    4.[python](python/) 文件夹由于本仓库为python，不再加入，后期适配

## 较大修改

* 删除 vendor/group
* schemastery包改为手搓校验包

## 更新日志

进行中:
* 初步重构：目前部分完成`packages/`的整理
* 彻底重构外部依赖(Cordis相关)：将`timer`合并进`cordis`；多个工具文件及`cosmokit`合并为一个工具文件；重写`schemastery`
* 优化原生体验：可安装为包，完成部分基础文件，下一步为正常导入

计划中(TODO):
* 完成web端并成功启动
* 跟上版本(进入0.1.1)

已完成:
3.初步重构外部依赖(Cordis相关)
2.将文档整理：`docs/`->`文档/官方文档/`
1.将大部分核心源码转为python版：`packages/`->`源码/`
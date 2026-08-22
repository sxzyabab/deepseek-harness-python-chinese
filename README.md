# Deepseek Harness Python (中文学习版)

**此仓库非官方仓库**（ 官方仓库: https://github.com/deepseek-ai/deepseek-harness ）

此仓库为官方deepseek harness的python版，大部分代码由**AI翻译**，并由**人工润色**

为了便于研究，该仓库采用全中文设计，**部分内容有删改**，需要原文请至官方仓库寻找

该仓库目前无法直接运行,在之后的版本会修复

## 文件导览

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
    4.[python](python/) 文件夹由于本仓库为python,不再加入,后期适配

## 较大修改

* 删除 vendor/group

## 更新日志

(计划)5.彻底重构外部依赖
(进行中)4.初步重构

3.初步重构外部依赖(Cordis生态)
2.将文档整理
1.将大部分核心源码转为python版
# MOSEC-PIP-PLUGIN

用于检测python项目的第三方依赖组件是否存在安全漏洞。

该项目是基于 [snyk-python-plugin](https://github.com/snyk/snyk-python-plugin.git) 的二次开发。

## 版本支持

Python 3.x

## 安装

```
pip install git+https://github.com/momosecurity/mosec-pip-plugin.git
```

## 使用

首先运行 [MOSEC-X-PLUGIN Backend](https://github.com/momosecurity/mosec-x-plugin-backend.git)

```
> cd your_python_project_dir/
> mosec requirements.txt --endpoint http://127.0.0.1:9000/api/plugin --only-provenance

// 或
> mosec setup.py --endpoint http://127.0.0.1:9000/api/plugin --only-provenance
```

## 卸载

```
> pip uninstall mosec-pip-plugin
```

## 开发

#### Pycharm 调试 mosec-pip-plugin

程序入口位于`mosec/pip_resolve.py`文件的`main()`函数
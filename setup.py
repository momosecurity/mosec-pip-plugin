from setuptools import setup, find_packages

setup(
    name="mosec-pip-plugin",
    version="1.1.1",
    author="retanoj",
    author_email="mmsrc@immomo.com",
    description="用于检测python项目的第三方依赖组件是否存在安全漏洞",
    license="Apache License 2.0",
    url="",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'Natural Language :: Chinese',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
    ],
    entry_points={
        'console_scripts': ['mosec=mosec.pip_resolve:main'],
    },
    zip_safe=True,
)

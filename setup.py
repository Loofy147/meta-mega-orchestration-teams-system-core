from setuptools import setup, find_packages

setup(
    name='meta_orchestration_core',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'python-dotenv',
        'redis',
    ],
    entry_points={
        'console_scripts': [
            'orchestration-listener=src.ct_002_data_processor:start_mq_listener',
            'resource-reporter=scripts.dt_001_resource_reporter:generate_report_and_publish',
            'security-auditor=src.st_001_config_auditor:run_security_audit',
            'pdf-generator=src.rt_001_pdf_generator:generate_pdf_report',
        ],
    },
    author='Meta Mega Orchestration Teams',
    description='Core processing and reporting module for the Meta Mega Orchestration System.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Loofy147/meta-mega-orchestration-teams-system-core',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    python_requires='>=3.8',
)

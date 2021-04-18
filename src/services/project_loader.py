import os
import pathlib
from typing import Optional, Callable, List

import cflib.bootloader
import cflib.crtp
import docker

import logging

from src.models.software_update import ProjectType, LogType


class ProjectLoader:
    client = docker.from_env()
    cwd = pathlib.Path.cwd()
    firmwarePath = cwd / '..' / 'firmware'
    volumes = {
        str(cwd / '..' / '.git'): {
            'bind': '/.git',
            'mode': 'ro',
        },
        str(firmwarePath): {
            'bind': '/firmware',
            'mode': 'ro',
        },
        str(cwd / 'out'): {
            'bind': '/out',
            'mode': 'rw',
        },
    }

    container_image = 'firmware'
    container_name = 'firmware_cload' # TODO: randomize
    lastProjectType: Optional[ProjectType] = None

    targets = [cflib.bootloader.Target('cf2', 'stm32', 'fw')] # noqa

    sandboxSrc = firmwarePath / 'projects' / 'sandbox' / 'src' / 'main.cpp'

    def __init__(self, logCb: Callable[[LogType, str], None],
                 bin: pathlib.Path = cwd / 'out' / 'cf2.bin'):
        logging.info(f'Current working directory is {ProjectLoader.cwd}')
        self.logCb = logCb
        self.bin = bin

        # TODO: check if directory out exists
        # if not, create it

    @staticmethod
    def createContainer(projectType: ProjectType):
        environment = {
            'CF2_PROJECT': projectType,
        }
        return ProjectLoader.client.containers.create(
            ProjectLoader.container_image,
            environment=environment,
            # firmware=rr
            labels={ProjectLoader.container_name: projectType},
            volumes=ProjectLoader.volumes
        )

    @staticmethod
    def getContainer(projectType: ProjectType):
        containers = ProjectLoader.client.containers.list(
            all=True,
            filters={
                'label': [
                    ProjectLoader.container_name + '=' + projectType
                ]
            })
        return containers[0] if len(containers) != 0 \
            else ProjectLoader.createContainer(projectType)

    def setup(self, projectType: ProjectType, code: Optional[str]
              ) -> bool:
        if projectType == 'sandbox':
            with ProjectLoader.sandboxSrc.open('w') as out:
                out.write(code)

        container = ProjectLoader.getContainer(projectType)
        logsIt = container.attach(stream=True)
        container.start()

        # blocking
        for log in logsIt:
            self.logCb('info', log.decode('utf-8'))

        # container.reload()
        # container.attrs['State']['ExitCode']

        result = container.wait()
        err = result['Error']
        if err is not None:
            self.logCb('error', f'Container failed with error {err}!')
            return False

        statusCode = result['StatusCode']
        if statusCode != 0:
            self.logCb(
                'error',
                f'Compilation failed! (exit status code is {statusCode})')
            return False

        self.logCb('success', 'Code compiled successfully')

        if not self.bin.exists():
            self.logCb('error', f'Executable {self.bin} not found!')
            return False

        if not os.access(self.bin, os.X_OK):
            self.logCb('error', f'File {self.bin} is not executable!')
            return False

        return True

    def flash(self, clinks: List[str]):
        for clink in clinks:
            self.logCb('info', f'Flashing {clink}...')
            bl = cflib.bootloader.Bootloader(clink)

            try:
                ok = bl.start_bootloader(warm_boot=True)
            except AttributeError:
                self.logCb('error', f'...bad clink provided')
                continue

            if not ok:
                self.logCb('error', f'...failed to warm boot')
                continue

            bl.flash(self.bin, ProjectLoader.targets)
            bl.reset_to_firmware()

            bl.close()
            self.logCb('success', f'...success')

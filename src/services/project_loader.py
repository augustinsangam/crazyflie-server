import logging
import os
import pathlib
from typing import List, Optional

import cflib.bootloader
import cflib.crtp
import docker
from src.models.software_update import ProjectType
from src.utils.setup_logging import SUCCESS_LEVEL_NUM


class ProjectLoader:
    client = docker.from_env()
    cwd = pathlib.Path.cwd()
    firmwarePath = cwd / '..' / 'firmware'
    outPath = cwd / 'out'
    volumes = {
        # str(cwd / '..' / '.git'): {
        #    'bind': '/.git',
        #    'mode': 'ro',
        # },
        # str(firmwarePath): {
        #    'bind': '/firmware',
        #    'mode': 'ro',
        # },
        # str(outPath): {
        #    'bind': '/out',
        #    'mode': 'rw',
        # },
    }

    containerImage = 'firmware_image'
    containerName = 'firmware_cload'
    lastProjectType: Optional[ProjectType] = None

    targets = [cflib.bootloader.Target('cf2', 'stm32', 'fw')]  # noqa

    sandboxSrc = firmwarePath / 'projects' / 'sandbox' / 'src' / 'main.cpp'

    def __init__(self, cf2_bin: pathlib.Path = cwd / 'out' / 'cf2.bin'):
        logging.info(f'Current working directory is {ProjectLoader.cwd}')
        self.bin = cf2_bin
        if not ProjectLoader.outPath.is_dir():
            ProjectLoader.outPath.mkdir()

    @staticmethod
    def createContainer(projectType: ProjectType):
        """Create a docker container for the given project type.

          @param projectType: the type of the project to create a container for.
        """
        environment = {
            'CF2_PROJECT': projectType,
        }
        return ProjectLoader.client.containers.create(
            ProjectLoader.containerImage,
            environment=environment,
            # firmware=rr
            labels={ProjectLoader.containerName: projectType},
            volumes=ProjectLoader.volumes,
            volumes_from=['firmware_container']
        )

    @staticmethod
    def getContainer(projectType: ProjectType):
        """Returns the container with the same given project type, or create a new one.

          @param projectType: the project type of the container searched.
        """
        containers = ProjectLoader.client.containers.list(
            all=True,
            filters={
                'label': [
                    ProjectLoader.containerName + '=' + projectType
                ]
            })
        return containers[0] if len(containers) != 0 \
            else ProjectLoader.createContainer(projectType)

    def setup(self, projectType: ProjectType, code: Optional[str]
              ) -> bool:
        """Run and try to build the code given in a container for the given project type.

          @param projectType: the type of the project to execute.
          @param code:the code to compile.
        """
        if projectType == 'sandbox':
            with ProjectLoader.sandboxSrc.open('w') as out:
                out.write(code)

        container = ProjectLoader.getContainer(projectType)
        logsIt = container.attach(stream=True)
        container.start()

        # blocking
        for log in logsIt:
            logging.info(log.decode('utf-8'))

        # container.reload()
        # container.attrs['State']['ExitCode']

        result = container.wait()
        err = result['Error']
        if err is not None:
            logging.error(f'Container failed with error {err}!')
            return False

        statusCode = result['StatusCode']
        if statusCode != 0:
            logging.error(
                f'Compilation failed! (exit status code is {statusCode})')
            return False

        logging.log(SUCCESS_LEVEL_NUM, 'Code compiled successfully')

        if not self.bin.exists():
            logging.error(f'Executable {self.bin} not found!')
            return False

        if not os.access(self.bin, os.X_OK):
            logging.error(f'File {self.bin} is not executable!')
            return False

        return True

    def flash(self, clinks: List[str]):
        """Try to flash the drone with the compilated code.

          @param clinks: the compilated code.
        """
        for clink in clinks:
            logging.info(f'Flashing {clink}...')
            bl = cflib.bootloader.Bootloader(clink)

            try:
                ok = bl.start_bootloader(warm_boot=True)
            except AttributeError:
                logging.error(f'...bad clink provided')
                continue

            if not ok:
                logging.error(f'...failed to warm boot')
                continue

            bl.flash(self.bin, ProjectLoader.targets)
            bl.reset_to_firmware()

            bl.close()
            logging.log(SUCCESS_LEVEL_NUM, f'...success')

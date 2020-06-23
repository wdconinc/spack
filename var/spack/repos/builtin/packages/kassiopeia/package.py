# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Kassiopeia(CMakePackage):
    """Simulation of electric and magnetic fields and particle tracking."""

    homepage = "https://katrin-experiment.github.io/Kassiopeia/"
    url      = "https://github.com/KATRIN-Experiment/Kassiopeia/archive/v3.6.1.tar.gz"
    git      = "https://github.com/KATRIN-Experiment/Kassiopeia.git"

    maintainers = ['wdconinc']

    version('master',  branch='master')
    version('3.6.1', sha256='30193d5384ad81b8570fdcd1bb35b15cc365ab84712819ac0d989c6f5cf6f790')
    version('3.5.0', sha256='b704d77bd182b2806dc8323f642d3197ce21dba3d456430f594b19a7596bda22')
    version('3.4.0', sha256='4e2bca61011e670186d49048aea080a06c3c95dacf4b79e7549c36960b4557f4')

    variant("root", default=False,
            description="Include support for writing ROOT files")
    variant("vtk", default=False,
            description="Include visualization support through VTK")
    variant("mpi", default=False,
            description="Include MPI support for field calculations")
    variant("tbb", default=False,
            description="Include Intel TBB support for field calculations")
    variant("opencl", default=False,
            description="Include OpenCL support for field calculations")

    depends_on('zlib')
    depends_on('root', when='+root')
    depends_on('vtk', when='+vtk')
    depends_on('openmpi', when='+mpi')
    depends_on('intel-tbb', when='+tbb')
    depends_on('opencl', when='+opencl')

    def cmake_args(self):
        args = []
        if self.spec.variants['vtk']:
            args.extend(['-DKASPER_USE_VTK=ON'])
        if self.spec.variants['tbb']:
            args.extend(['-DKASPER_USE_TBB=ON'])
        if self.spec.variants['mpi']:
            args.extend(['-DKEMField_USE_MPI=ON'])
        if self.spec.variants['vtk']:
            args.extend(['-DKEMField_USE_OPENCL=ON'])
        return args

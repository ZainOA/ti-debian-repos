#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "run.sh: missing operands"
    echo "Requires source package name as argument"
    exit 1
fi

topdir=$(git rev-parse --show-toplevel)
projdir="${topdir}/$1"
builddir="${topdir}/build/$1"
sourcedir="${builddir}/sources"

if [ ! -d ${projdir} ]; then
    echo "This project does not exist."
    echo "Exiting."
    exit 1
fi

cd ${projdir}/suite/bookworm/
package_name=$(dpkg-parsechangelog --show-field Source)
deb_version=$(dpkg-parsechangelog --show-field Version)
package_version=$(echo $deb_version | cut -d'-' -f1)
package_full="${package_name}-${package_version}"
package_full_ll="${package_name}_${package_version}"
echo "Building " $package_name " version " $deb_version
cd -

source ${projdir}/version.sh

mkdir -p ${builddir}

if $custom_build ; then
    run_custom_build
    exit 0
fi

if [ $require_root = "true" ] && [ "$EUID" -ne 0 ] ; then
    echo "Requires root privileges to execute"
    echo "Exiting"
    exit 1
fi

mkdir -p "${sourcedir}"

cd ${builddir}
if [ ! -f "${package_full_ll}.orig.tar.gz" ]; then
    cd "${sourcedir}"
    if [ ! -d "${package_full}" ]; then
        git clone "${git_repo}" "${package_full}"
    fi
    cd "${package_full}"
    git checkout "${last_tested_commit}"
    cd -
    tar -cvzf "${builddir}/${package_full_ll}.orig.tar.gz" "${package_full}"
    cd ${builddir}
    tar -xzmf "${package_full_ll}.orig.tar.gz"
fi

cd "${builddir}/${package_full}"
if [ ! -d "debian" ]; then
	debmake
fi

# Deploy our Debian control files
cp -rv "${projdir}/suite/bookworm/debian" "${builddir}/${package_full}/"

run_prep

# Apply un-applied Debian patches
patch_dir="${builddir}/${package_full}/debian/patches"
while read -r patch; do
    if [ -f "${builddir}/series" ]; then
        if ! grep -Fxq "$patch" "${builddir}/series" ; then
            continue
        fi
    fi
    git apply --check "${patch_dir}/${patch}" --verbose --reject
done < "${patch_dir}/series"
cp "${patch_dir}/series" "${builddir}"

debuild --no-lintian

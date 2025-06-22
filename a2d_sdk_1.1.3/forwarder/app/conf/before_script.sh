#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

export PS4='+ ${BASH_SOURCE}:${LINENO}: '
set -x

export GIT_PROJECT_NAME=$(basename `git remote -v | awk '/origin.*(fetch)/{print $2}' | sed 's/.*\/\([^ ]*\/[^ .]*\).*/\1/'`)
export PROJECT_ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export PROJECT_FOLDER=${PROJECT_ROOT_DIR}
export CI_HELPER_SRC_DIR=${PROJECT_ROOT_DIR}/ci_helper # 可通过环境变量设置

function print_help() {
    echo -e "
    ${GREEN}Build CoSine Project

    Note:
    - DriveOS, CUDA must be installed with SDK Manager:
        $HOME/nvidia/nvidia_sdk/DRIVE_OS_5.2.3_SDK_Linux_OS_DDPX
        /usr/local/cuda-10.2
        refer to:
        https://docs.nvidia.com/drive/drive-os-5.2.0.0L/drive-qsg-dz/install-with-sdkm-drive/index.html

    support command examples:
    cppcheck command:
        ./build.sh cppcheck ./

    ci build command:
        ./build.sh x86 debug compile
        ./build.sh x86 release compile
        ./build.sh aarch64 debug compile
        ./build.sh aarch64 release compile
        ./build.sh x86 debug package
        ./build.sh x86 release package
        ./build.sh aarch64 debug package
        ./build.sh aarch64 release package

    conan build command:
        this must set env with \" export BUILD_WITH_CONAN=TRUE \" before build
        ./build.sh make x86_64 debug
        ./build.sh make x86_64 release
        ./build.sh make orin debug
        ./build.sh make orin release

    local build command:
        ./build.sh make aarch64 debug
        ./build.sh make x86 release
        ./build.sh clean
        ./build.sh install x86 debug
        ./build.sh install aarch64 release
        ./build.sh publish x86 debug
        ./build.sh publish aarch64 release

    Maintainers:
    - yang.yang
    ${NC}
    "
    exit 0
}

function git_handle_ci_helper() {
    local input_ref=develop
    local input_commit_id=""
    if [ ! -z ${ci_helper_build_branch} ]; then input_ref=${ci_helper_build_branch} ; fi
    if [ ! -z ${ci_helper_build_commit_id} ]; then input_commit_id=${ci_helper_build_commit_id}; fi
    echo "Use ci_helper[${CI_HELPER_SRC_DIR}] build rep, branch:${input_ref}, commit id:${input_commit_id}"

    if [ ! -d "${CI_HELPER_SRC_DIR}" ]; then  # clone conan_suite if conan_suite is not in current repo
        git clone -q -b ${input_ref} https://oauth2:glpat-Px4zWSczBS-3yhKki-B4@code.agibot.com/agibot_devops/ci_helper.git ${CI_HELPER_SRC_DIR}
    else
        local -r git_config="--git-dir=${CI_HELPER_SRC_DIR}/.git --work-tree=${CI_HELPER_SRC_DIR}"
        local repo_branch="$(git ${git_config} rev-parse --abbrev-ref HEAD)"
        if [ "${repo_branch}" == "HEAD" ]; then  # HEAD detached at (commit or tag)
            # shellcheck disable=SC2076
            if [[ -n "${input_commit_id}" && "$(git ${git_config} rev-parse HEAD)" =~ "${input_commit_id}" ]]; then return 0; fi  # repo_commit_id is identical with input commit_id
            if [ "$(git ${git_config} tag -l --sort=creatordate --points-at | tail -n 1)" == "${input_ref}" ]; then return 0; fi  # repo_tag is identical with input ref
        fi
        #if [ "${repo_branch}" == "${input_ref}" ]; then
        #    git ${git_config} pull -q origin ${input_ref}
        #else
        #    git ${git_config} fetch -q origin ${input_ref}; git ${git_config} checkout -q ${input_ref}
        #fi
    fi
    if [ -n "${input_commit_id}" ]; then git ${git_config} checkout -q ${input_commit_id}; fi
}

git_handle_ci_helper    # git clone or pull ci_helper from remote
# shellcheck disable=SC2068

# pass a dest path
if [ ! -z ${DEST_PATH} ]; then dest_path=${DEST_PATH}; else dest_path=${PROJECT_ROOT_DIR}; fi
cp -af ${CI_HELPER_SRC_DIR}/conanfile.py ${dest_path}
echo "Copy conanfile.py From[${CI_HELPER_SRC_DIR}] To[${dest_path}]"

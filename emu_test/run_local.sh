#!/bin/bash
# This script should allow you to run the CTS tests from a local linux box.
# In order to run this test you will have to have:
#
# - A working emulator build
# - A proper cts plan, you can use the default one this branch if you wish
# - A directory containing a cts distribution available at:
#   https://source.android.com/compatibility/cts/downloads.html
# - Have ANDROID_SDK_ROOT properly set
#
# You can edit config/local_cfg.csv to indicate which images you would like to
# run the cts against. Note that the images will be picked up from the default
# ANDROID_SDK_ROOT path.
#
#
# By default it will create a virtual python environment and install the latest
# psutils, and requests after which it will invoke the tests
#
# One way of using this script is to add it to your crontab. For example:
# 19 14   * * *   jansene export DISPLAY=:0; \
#  export ANDROID_SDK_ROOT=$HOME/Android/Sdk; \
#  $HOME/src/droid/emu-master-dev02/external/adt-infra/emu_test/run_local.sh \
#  --local-build --get-cts  >> /tmp/errlog.txt 2>&1
#
# To make sure the run will terminate (the tests sometimes get stuck) it is wise
# to add an entry to kill the process
# 08 02 * * * jansene pkill run_local

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f ${dir}../../qemu/objs/emulator ]; then
  option_emu_exec=$(realpath ${dir}/../../qemu/objs/emulator)
else
  option_emu_exec=emulator
fi
option_emu_test=boot,cts
option_python=python
option_cts_dir=~/android-cts
option_cts_plan=${dir}/test_cts/tests
option_result_dest=${dir}
option_emu_img=latest
option_cts_build=latest
option_emu_build="local"
option_local_build=no

red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`

# Parse out the options
for opt; do
  optarg=`expr "x$opt" : 'x[^=]*=\(.*\)'`
  case $opt in
    -h|--help|-\?) option_help=yes;;
    --tests*) option_emu_test=${optarg};;
    --cts-plan*) option_cts_plan=${optarg/#\~/$HOME} ;;
    --cts-build*)  option_cts_build=${optarg} ;;
    --img-build*) option_emu_img=${optarg} ;;
    --emu-build*) option_emu_build=${optarg} ;;
    --cts-module*) option_cts_module=${optarg} ;;
    --dir*) artifact_dir=${optarg/#\~/$HOME} ;;
    *)
    echo "unknown option '$opt', use --help"
    exit 1
    ;;
  esac
done

if [ "$option_help" = "yes" ] ; then
    echo "Usage: run_local.sh [options]"
    echo
    echo "Options: [defaults in brackets after descriptions]"
    echo ""
    echo "Standard options:"
    echo "  --help                      Print this message"
    echo "  --tests=...                 List of test types to run [$option_emu_test]"
    echo "  --cts-plan=...              Directory containing the CTS.xml plan [$option_cts_plan]"
    echo "  --dir=...                   Directory to copy artifacts to, you will find cts results here as well. [/tmp/.....]"
    echo "  --cts-build=...             Build number to fetch from build [latest]"
    echo "  --img-build=...             Build number to fetch from build server, will overwrite your existing emulator 24 image. [latest]"
    echo "  --emu-build=...             Build number to fetch from build server containing the emulator, or local for local build  [local]"
    echo "  --cts-module=..             Run the given cts module, no other tests will be run"
    echo
    echo "Setting the build to none, will prevent any downloads and installs. It will re-use the existing artifacts."
    echo
    echo "Make sure you have the following images available: "
    tail -n +3 config/local_cfg.csv  | awk -F "," '{ print $1 }'
    echo
    echo "Note that your existing artifact directory will not be overwritten, so you can still find your results in the directory"
    exit 1
fi

if [ -z ${ANDROID_SDK_ROOT} ]; then
  echo >&2 "You need to set ANDROID_SDK_ROOT!"
  exit 1
fi

# Setup paths, so the tests can access mksdcard, adb and can compile things
# through gradle.
export PATH=$PATH:$ANDROID_SDK_ROOT/tools:$ANDROID_SDK_ROOT/platform-tools
export ANDROID_HOME=$ANDROID_SDK_ROOT

if [ -z ${artifact_dir} ]; then
  artifact_dir=$(mktemp -d /tmp/emu-test-artifacts-XXXXXXXXXXX)
fi

mkdir -p $artifact_dir

# Fetches an artifact from the build servers.
fetch_artifact() {
  bid=$1
  branch=$2
  target=$3
  artifact=$4
  dest=$5

  if [ "$bid" == "none" ]; then
    echo "${green}Re-using artifact ${artifact}${reset}"
    return
  fi

  echo "${green}Fetching artifact ${artifact} with ${bid} from ${branch} to ${dest} ${reset} "

  pushd $artifact_dir > /dev/null
  if [ "${bid}" == "latest" ]; then
    /google/data/ro/projects/android/fetch_artifact --latest --branch "${branch}" --target "${target}" "${artifact}" || exit 1
  else
    /google/data/ro/projects/android/fetch_artifact --bid "${bid}" --target "${target}" "${artifact}" || exit 1
  fi

  mkdir -p "${dest}"
  zip=$(find $artifact_dir -name $artifact | tail -n 1)
  unzip -o -q "${zip}" -d "${dest}"
  rm -f "${zip}"

  popd > /dev/null
}


setup_venv() {
  # Setup the virtual python env.
  if [ ! -f "${dir}/venv/bin/activate" ]; then
    virtualenv ${dir}/venv
    . ${dir}/venv/bin/activate
    pip install psutil requests
  else
    . ${dir}/venv/bin/activate
  fi

  option_python=${dir}/venv/bin/python
}

# Function that executes the whole test suite using our test runners.
run_test_suite() {
  # loop and run all the tests
  log_dir="${artifact_dir}/stdio-"$(date -d "today" +"%Y%m%d%H%M")
  mkdir -p $log_dir
  for test in $(echo $option_emu_test| sed "s/,/ /g")
  do
    echo "${green}Running the ${test} tests${reset}"
    tests="test_${test}.*"

    $option_python $dir/dotest.py --config_file $dir/config/local_cfg.csv  --buildername 'localhost' --file_pattern $tests --emulator $option_emu_exec  --cts-dir ${option_cts_dir} --cts-plan ${option_cts_plan} --cts-module ${option_cts_module} | tee "${log_dir}/${test}"

  done
}

# Setup emulator.
if [ "${option_emu_build}" = "local" ] ; then
    echo "${green}Building the emulator${reset}"
    ${dir}/../../qemu/android/rebuild.sh || (echo "${red}Failed to build emulator!"; exit 1)
    option_emu_exec=$(realpath ${dir}/../../qemu/objs/emulator)
else
  ctsemu="${artifact_dir}/emulator"
  fetch_artifact ${option_emu_build} aosp-emu-master-dev sdk_tools_linux 'sdk-repo-linux-emulator-*.zip' $ctsemu
  option_emu_exec=$ctsemu/emulator/emulator
fi

if [ ! -f ${option_emu_exec} ]; then
  echo >&2 "The emulator executable [$option_emu_exec] is not on the path"
  exit 1
fi

echo "${green}Using emulator ${option_emu_exec}${reset}"

# Download cts if needed.
if [ ! -z ${option_cts_build} ]; then
  fetch_artifact ${option_cts_build} git_oc-release cts_x86_64 'android-cts.zip' ${artifact_dir}
  option_cts_dir="${artifact_dir}/android-cts"
fi

# Download image
if [ ! -z ${option_emu_img} ]; then
  echo "${red}WARNING WARNING WARNING WARNING, this will overwrite your android-24 image with build: ${option_emu_img} !!${reset}"
  fetch_artifact ${option_emu_img} git_oc-emu-dev sdk_gphone_x86-user 'sdk-repo-linux-system-images-*.zip' ${ANDROID_SDK_ROOT}/system-images/android-24/google_apis
fi

# Make sure the tools directory of the android_sdk_root is on the path so we can
# call mksdcard and aapt from within the python scripts.
AAPT=$(find $ANDROID_SDK_ROOT -name 'aapt' -type f | tail -n 1)
AAPT_DIR=$(dirname $AAPT)
PATH=${ANDROID_SDK_ROOT}/tools:${ANDROID_SDK_ROOT}/platform-tools:$AAPT_DIR:$PATH

setup_venv

if [ ! -z "$option_cts_module" ]; then
  option_emu_test=module
fi

run_test_suite


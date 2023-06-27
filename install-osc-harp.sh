#!/bin/bash

source install-script-source/install-template.sh

if [ -z "$1" ]; then RUNTIME_ENV="harp_env"; else RUNTIME_ENV=$1; fi

pwdir=`pwd`

VERIFY_FILES="
cheetah/bin/cheetah
"

MULTISTEPS="" 
initialize harp 1.1.0

find_conda_exists(){
    which conda | grep -o /conda > /dev/null &&  echo 0 || echo 1
}

find_in_conda_env(){
    conda env list | grep -o $RUNTIME_ENV> /dev/null && echo 0 || echo 1
}

find_harp_version(){
    module use $HOME/osc_apps/lmodfiles
    module load harp 
    module --redirect list | grep -o harp/1.0.0> /dev/null && echo 0 || echo 1
    module unload harp/1.0.0
}

# [REQUIRED] if MODULE_SETTING is not only
obtain_src() {
  # Download your source code in this step
  # You can use the variable `dldir` as the location
  #   to which the files should be downloaded
  # A typical command would look like the following:
  echo ""
}

# [REQUIRED] if MODULE_SETTING is not only
setup_step() {
  # Any steps to process the files obtained in `obtain_src`
  #   before they are ready to be configured
  # The variable `srcdir` contains the location where
  #   the ready-to-configure files should be placed
  # For example, if you downloaded a tarball in the `obtain_src` step,
  #   you should probably extract it here
  echo ""
}

# [REQUIRED] if MODULE_SETTING is not only
configure_step() {
  # Any steps required to configure the source code before it can be compiled
  # The `builddir` variable contains the location of a subdirectory of `srcdir`
  #   in which you can build out-of-tree
  # The `installdir` variable contains the location of the final install directory
  # A typical configure command(s) will be similar to the following:
  
  echo "Step 1: Configuring the conda environmnet"
  echo  "Install folder: $installdir"
  if [ ! -d "$HOME/miniconda3" ] 
  then 
    echo "conda doesnot exists"
    # wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -P $installdir
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -P $installdir
    bash $installdir/Miniconda3-latest-Linux-x86_64.sh
    echo "conda is installed"
    rm -rf $installdir/Miniconda3-latest-Linux-x86_64.sh
  fi
  source $HOME/miniconda3/bin/activate
  #source $installdir/miniconda3/bin/activate
  
  
  # Changes 1 START
  echo "Installing here: '$pwdir' with env '$RUNTIME_ENV'"
  echo "Finding Conda env '$RUNTIME_ENV' (0-exists, 1-does not exist) : $(find_in_conda_env)"
  if [ $(find_in_conda_env) == 1 ] 
  then
    echo "conda env doesnot exist, we will set up an environment $RUNTIME_ENV";
    setup_conda_env="y"
  else
    echo "conda env $RUNTIME_ENV exists, type 1 to use $RUNTIME_ENV or 2 to enter to exit"
    setup_conda_env="n"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) break;;
            No ) echo "Exiting the setup, try re-installing with ' ./install-osc-harp.sh <new-env-name>'"; exit;;
        esac
    done
  fi
  
  if [ $setup_conda_env == "n" ]
  then
    echo "Step2: Checking if HARP is previously Installed with dependencies"
    if [ $(find_harp_version) == 1 ] 
    then
        echo "HARP was not previously installed, we will install HARP v1.1.0 with $RUNTIME_ENV environment";
        harp_installed="n"
    else
        echo "Upgrading HARP to v1.1.0 with $RUNTIME_ENV environment";
        harp_installed="y"
    fi
  else
    harp_installed="n"
  fi
  
  
  
  if [ $setup_conda_env == "y" ]
  then
      # COMPLETE FRESH INSTALL START
      echo "1. Setting up conda environment..."
      conda create --name $RUNTIME_ENV python=3.9
      conda activate $RUNTIME_ENV
      echo "DONE conda env is setup and activated"
  else
      echo "--------------------conda activate $RUNTIME_ENV"
      conda activate $RUNTIME_ENV
      echo "DONE conda env is activated"
  fi
  
  if [ $harp_installed == "n" ]
  then
      
      echo "2. Installing CODAR Cheetach "
      cp -r $srcdir/cheetah $installdir
      # cd $srcdir/cheetah 
      cd $installdir/cheetah
      pip install --editable .
      echo "DONE cheetah is configured"
    
      echo "3. Installing tensorflow and other dependecies for the pipeline"
      conda install -c anaconda tensorflow-gpu
      conda install -c conda-forge psutil
      conda install pandas
      conda install scikit-learn
      echo "DONE installing tensorflow and other dependecies for the pipeline"
    
      #Copy Pipeline to install directory
      echo "4. Copying and cofiguring HARP pipeline"
      cp -r $srcdir/pipeline $installdir/
      mkdir $installdir/bin
      cp $srcdir/pipeline/bin/OSC/harp $installdir/bin
      echo "DONE Copying HARP pipeline"
      
      # COMPLETE FRESH INSTALL END
      
  else
    if [ $harp_installed == "y" ]
    then
        echo "Updating files for HARP Version 1.1.0"
        
        echo "1. Updating CODAR Cheetach "
        cp -r $srcdir/cheetah $installdir
        cd $installdir/cheetah
        pip install --editable .
        echo "DONE cheetah is configured"
        
        #Copy Pipeline to install directory
        echo "4. Copying and cofiguring HARP pipeline"
        cp -r $srcdir/pipeline $installdir/
        mkdir $installdir/bin
        cp $srcdir/pipeline/bin/OSC/harp $installdir/bin
        echo "DONE Copying HARP pipeline"
    fi
  fi
  
  # Changes 1 END

 

}

# [REQUIRED] if MODULE_SETTING is not only
make_step() {
  # Any steps required to build/compile the software
  # A typical build command(s) will be similar to the following:
  echo "make_step"
  #make
}

# [REQUIRED] if MODULE_SETTING is not only
make_install_step() {
  # Any steps required to install the compiled software
  # A typical install command(s) will be similar to the following:
  echo "make_install_step"
  #make install
}


generate_module_file() {
  # Our simple example package builds an shared library
  #   and an executable that links against the shared library
  # So our module file needs to put them on `PATH` and `LD_LIBRARY_PATH`, respectively
cat <<EOF >>$modfile
prepend_path("PATH", root .. "/bin")
prepend_path("LD_LIBRARY_PATH", root .. "/lib")
EOF
}

# Perform the installation 
do_install

# Perform post-processing
finalize

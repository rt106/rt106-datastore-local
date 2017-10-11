#!/bin/sh

download_option=$DOWNLOAD_RAD_DEMO_DATA

download_dir=$PWD/rad_demo_data

dir_patient1="/rt106/data/Patients/Adam/Primary/Imaging"
dir_patient2="/rt106/data/Patients/Eve/Primary/Imaging"
count1=0
count2=0
# If we already downloaded the dataset, check the number of files to see if we need to download again
# for Adam, number of files is 705; for Eve, number of files is 684.
if [ -d "$dir_patient1" ]; then
  count1=$(find ${dir_patient1} -type f | wc -l)
fi
if [ -d "$dir_patient2" ]; then
  count2=$(find ${dir_patient2} -type f | wc -l)
fi

if [ $count1 -ne 705 ] || [ $count2 -ne 684 ] || [ $download_option = 'force' ] ; then

  if [ ! -d "$download_dir" ] ; then
    mkdir "$download_dir"
    echo "create a directory for the downloaded data : $download_dir"
  fi

  cd $download_dir

  # download public dataset from Visible Human Project CT Datasets
  if [ $count1 -ne 705 ] || [ $download_option = 'force' ] ; then
    echo "downloading portion of Visible Human Male"
    curl -k -O https://mri.radiology.uiowa.edu/VHDicom/VHMCT1mm/VHMCT1mm_Head.tar.gz
    curl -k -O https://mri.radiology.uiowa.edu/VHDicom/VHMCT1mm/VHMCT1mm_Shoulder.tar.gz
  fi

  if [ $count2 -ne 684 ] || [ $download_option = 'force' ] ; then
    echo "downloading portion of Visible Human Female"
    curl -k -O https://mri.radiology.uiowa.edu/VHDicom/VHFCT1mm/VHF-Head.tar.gz
    curl -k -O https://mri.radiology.uiowa.edu/VHDicom/VHFCT1mm/VHF-Shoulder.tar.gz
  fi

fi

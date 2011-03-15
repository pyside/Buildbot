#!/bin/sh

arch=$1
module_libfile=$2
module_include_dir=$3
tmp_module_dir=$4

dir=/tmp/latest/$arch

rm -rf $dir/$tmp_module_dir
mkdir -p $dir/$tmp_module_dir/lib
mkdir -p $dir/$tmp_module_dir/include/$module_include_dir

cp /usr/include/$module_include_dir/*.h $dir/$tmp_module_dir/include/$module_include_dir
cp /usr/lib/$module_libfile $dir/$tmp_module_dir/lib

cd $dir
tar cvf $tmp_module_dir.tar $tmp_module_dir
gzip $tmp_module_dir.tar


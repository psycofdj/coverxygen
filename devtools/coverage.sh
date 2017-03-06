#!/bin/bash


l_path=$(readlink -f $0)
cd $(dirname $(dirname ${l_path}))
l_interpreter=$1

function join
{
  local IFS="$1";  shift;
  echo "$*";
}

function get_sources
{
  l_sources=$(find coverxygen -name '*.py' -a ! -name 'test_*')
  echo ${l_sources}
}

function get_source_dirs
{
  l_sources=$(get_sources)
  l_dirs=()
  for c_file in $(echo ${l_sources}); do
    l_dirs=(${l_dirs[@]} $(dirname ${c_file}))
  done
  l_list=$(echo ${l_dirs[@]} | sed 's/ /\n/g' | sort -u | tr '\n' ' ')
  join , ${l_list}
}

function gen_cov
{
  rm -f .coverage
  $1 -m coverage run --source "$(get_source_dirs)" --omit "coverxygen/test/*" --branch ./devtools/unittests.py
}


gen_cov ${l_interpreter}

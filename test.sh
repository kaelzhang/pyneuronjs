#!/bin/bash

#
# Log <type> <msg>
#

log() {
  printf "\033[36m%s\033[0m : \033[90m%s\033[0m\n" $1 $2
}

#
# Exit with the given <msg ...>
#

abort() {
  printf "\n\033[31mError: $@\033[0m\n\n" && exit 1
}

py='.py'
files=(module walker)
for file in ${files[@]}; do
  echo
  log "test" "$file$py"
  echo

  # Test the file as a package, to avoid the python import problem in a mess
  python "test/$file$py" || abort "test $file$py failed."
done

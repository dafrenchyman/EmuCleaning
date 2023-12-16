#!/bin/bash

zipSourceLocation="/zip/"
chdDestinationLocation="/chd/"

cd "${zipSourceLocation}"
for zipFile in *.zip; do
	gameName="$(basename "$zipFile" .zip)"
	cueFile="${gameName}.cue"
	echo "------------------------------------"
	echo "Converting ${gameName}..."
	echo "------------------------------------"
	mkdir -p "${gameName}"
	echo "unzipping..."
	unzip "${zipFile}" -d "${gameName}"
	echo "converting..."
	chdman createcd --force -i "${gameName}/${cueFile}" -o "${chdDestinationLocation}${gameName}.chd"
	echo "cleanup..."
	rm -rf "./${gameName}"
done

echo "All done."

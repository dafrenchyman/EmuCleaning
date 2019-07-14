#!/bin/bash
cd ./zip
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
	chdman createcd -i "${gameName}/${cueFile}" -o "../chd/${gameName}.chd"
	echo "cleanup..."
	rm -rf "./${gameName}"
done

echo "All done."
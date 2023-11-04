#!/bin/bash
gamesToCheck=""
for zipFile in *.zip; do
	gameName="$(basename "$zipFile" .zip)"
	echo "------------------------------------"
	echo "Checking ${gameName}..."
	echo "------------------------------------"
	unzip -l "${zipFile}"
done

echo "All done."

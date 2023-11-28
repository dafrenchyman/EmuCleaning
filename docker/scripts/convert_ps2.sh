#!/bin/bash
zipSourceLocation="/ROMs/7zipped_ps2/"
csoDestinationLocation="/ROMS/ps2/"

cd "${zipSourceLocation}"
for zipFile in *.7z; do
	gameName="$(basename "$zipFile" .7z)"

	echo "------------------------------------"
	echo "Converting ${gameName}..."
	echo "------------------------------------"

	# Get list of filenames in the zip file
	gameFileName=`7z -slt l "${zipFile}" | grep -oP "(?<=Path = ).+" | tail -n +2`
	nameInZip="$(basename "$gameFileName")"
	extensionInZip="${gameFileName##*.}"
	zipBaseName="${nameInZip%.*}"
	finalFilename="${destinationLocation}${gameName} [${zipBaseName}].chd"

	echo "Source file: ${zipSourceLocation}${zipFile}"
	echo "Original filename: ${gameFileName}"
	echo "Extension: ${extensionInZip}"
	echo "Destination: ${finalFilename}"

	# If we've already processed the file skip it
	if [[ -f "$finalFilename" ]]; then
		echo "Skipping game already prepared: ${finalFilename}"
		continue
	fi

	mkdir -p "${destinationLocation}${gameName}"
	echo "unzipping..."
	7z x -o"${destinationLocation}${gameName}" "${zipFile}"
	echo "converting..."

	cd "${destinationLocation}${gameName}"

	# If there are > 1 binFile, we can't process it yet
	numBinFiles=`find "${destinationLocation}${gameName}/" -mindepth 1 -maxdepth 1 -type f -name "*.bin" -printf x | wc -c`
	if [ $numBinFiles -ge 2 ]; then
	  echo "Cannot process cue/bin with > 1 bin file"
	  failedToProcess+=("${zipFile}")
    continue
  fi

	for binFile in *.bin; do
		[ -f "$binFile" ] || break
		echo "${binFile}"
		binName="$(basename "$binFile" .bin)"
		cueFilename="${binName}.cue"
		echo -e "FILE\"${gameFileName}\" BINARY\nTRACK 01 MODE2/2352\nINDEX 01 00:00:00" > "${destinationLocation}${gameName}/${cueFilename}"
		bchunk "${binName}.bin" "${binName}.cue" "${binName}"

		# bchunk adds a 01 (for the track number to the filename). Need to remove that
		bchunkName="${binName}01.iso"
		mv "${bchunkName}" "${binName}.iso"

	done

	for isoFile in *.iso; do
		isoName="$(basename "$isoFile" .iso)"
		newIsoFileName="${gameName} [${isoName}].iso"
		mv "${isoFile}" "${newIsoFileName}"

		newFileName="$(basename "$newIsoFileName" .iso).chd"
		chdman createcd -o "${newFileName}" -i "${newIsoFileName}"
		# ciso 9 "${newIsoFileName}" "${newFileName}"
		mv "${newFileName}" "../${newFileName}"

		# Delete the iso file
		rm "${newIsoFileName}"
	done
	echo "cleanup..."
	cd ..
	rm -rf "${destinationLocation}${gameName}"
	cd "${zipSourceLocation}"

done

echo "The following files couldn't be processed:"
for i in "${failedToProcess[@]}"; do
    echo "$i"
done

echo "All done."